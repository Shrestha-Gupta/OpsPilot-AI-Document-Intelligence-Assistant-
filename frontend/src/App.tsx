import { useState, useEffect, useCallback } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { ChatWindow } from './components/chat/ChatWindow';
import { documentsApi } from './api/documents';
import { conversationsApi } from './api/conversations';
import type { Document, Conversation, Message } from './types';

export function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // 1. Fetch initial documents and conversations
  const loadDocuments = useCallback(async () => {
    try {
      const data = await documentsApi.list();
      setDocuments(data);
    } catch (e: any) {
      console.error('Failed to load documents:', e);
    }
  }, []);

  const loadConversations = useCallback(async () => {
    try {
      const data = await conversationsApi.list();
      setConversations(data);
      if (activeConvId && !data.some((c) => c.id === activeConvId)) {
        // Active conversation was deleted or is stale
        setActiveConvId(data.length > 0 ? data[0].id : null);
      } else if (data.length > 0 && !activeConvId) {
        // Select latest conversation
        setActiveConvId(data[0].id);
      }
    } catch (e: any) {
      console.error('Failed to load conversations:', e);
    }
  }, [activeConvId]);

  useEffect(() => {
    loadDocuments();
    loadConversations();
  }, [loadDocuments, loadConversations]);

  // 2. Poll for documents in 'processing' or 'uploading' status
  useEffect(() => {
    const hasPending = documents.some(
      (d) => d.status === 'processing' || d.status === 'uploading'
    );
    if (!hasPending) return;

    const interval = setInterval(async () => {
      try {
        const data = await documentsApi.list();
        setDocuments(data);
      } catch (e) {
        console.error('Polling error:', e);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [documents]);

  // 3. Load active conversation messages
  useEffect(() => {
    if (!activeConvId) {
      setMessages([]);
      return;
    }

    let isMounted = true;
    conversationsApi
      .get(activeConvId)
      .then((conv) => {
        if (isMounted) {
          setMessages(conv.messages || []);
        }
      })
      .catch((err: any) => {
        if (!isMounted) return;
        if (err.response?.status === 404) {
          console.warn(`Conversation ${activeConvId} not found (404). Clearing stale active conversation.`);
          setActiveConvId(null);
          setMessages([]);
          loadConversations();
        } else {
          console.error('Failed to load messages:', err);
          const msg =
            err.response?.data?.message ||
            err.message ||
            'Failed to load messages for conversation';
          toast.error(msg);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [activeConvId, loadConversations]);

  // 4. Update suggested questions when ready documents change
  useEffect(() => {
    const readyDocs = documents.filter((d) => d.status === 'ready');
    if (readyDocs.length > 0 && suggestedQuestions.length === 0) {
      // Fetch suggestions for the first ready document
      documentsApi
        .getSuggestions(readyDocs[0].id)
        .then((suggestions) => {
          if (suggestions && suggestions.length > 0) {
            setSuggestedQuestions(suggestions);
          }
        })
        .catch(() => {});
    }
  }, [documents, suggestedQuestions.length]);

  // Handlers
  const handleToggleSelectDoc = (id: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSelectAllDocs = () => {
    const readyIds = documents.filter((d) => d.status === 'ready').map((d) => d.id);
    setSelectedDocIds(readyIds);
  };

  const handleDeselectAllDocs = () => {
    setSelectedDocIds([]);
  };

  const handleUploadFiles = async (files: File[]) => {
    setIsUploading(true);
    setUploadProgress(0);
    try {
      const res = await documentsApi.upload(files, (percent) => {
        setUploadProgress(percent);
      });
      toast.success(res.message);
      await loadDocuments();
    } catch (err: any) {
      const msg = err.response?.data?.message || err.message || 'Upload failed';
      toast.error(msg);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDeleteDocument = async (id: string) => {
    try {
      await documentsApi.delete(id);
      toast.success('Document deleted');
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      setSelectedDocIds((prev) => prev.filter((item) => item !== id));
    } catch (err: any) {
      toast.error('Failed to delete document');
    }
  };

  const handleAskAboutDoc = async (id: string) => {
    // Scope search specifically to this document
    setSelectedDocIds([id]);
    try {
      toast.loading('Fetching document suggestions...', { id: 'suggestions-load' });
      const suggestions = await documentsApi.getSuggestions(id);
      toast.dismiss('suggestions-load');
      setSuggestedQuestions(suggestions);
      toast.success('Questions loaded for document');
    } catch {
      toast.dismiss('suggestions-load');
      toast.error('Could not load suggestions');
    }
  };

  const handleNewChat = async () => {
    try {
      const newConv = await conversationsApi.create();
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([]);
      toast.success('Started new chat');
    } catch {
      toast.error('Failed to create new chat');
    }
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      await conversationsApi.delete(id);
      toast.success('Chat deleted');
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvId === id) {
        setActiveConvId(null);
        setMessages([]);
      }
    } catch {
      toast.error('Failed to delete conversation');
    }
  };

  const handleClearChat = async () => {
    if (!activeConvId) return;
    try {
      await conversationsApi.clearMessages(activeConvId);
      setMessages([]);
      toast.success('Chat messages cleared');
    } catch {
      toast.error('Failed to clear chat');
    }
  };

  const handleSendMessage = async (question: string) => {
    let convId = activeConvId;

    // If no active conversation, create one first
    if (!convId) {
      try {
        const newConv = await conversationsApi.create();
        setConversations((prev) => [newConv, ...prev]);
        convId = newConv.id;
        setActiveConvId(newConv.id);
      } catch {
        toast.error('Failed to start conversation');
        return;
      }
    }

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: convId,
      role: 'user',
      content: question,
      sources: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      // Scope document IDs: if none selected, search across all
      const payloadDocs = selectedDocIds.length > 0 ? selectedDocIds : undefined;
      const res = await conversationsApi.chat(convId, question, payloadDocs);

      const assistantMsg: Message = {
        id: res.message_id,
        conversation_id: res.conversation_id,
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        created_at: res.created_at,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      // Refresh conversations in case title was updated
      loadConversations();
    } catch (err: any) {
      const msg = err.response?.data?.message || err.message || 'Failed to get answer';
      toast.error(msg);
      // Remove optimistic user message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
    } finally {
      setIsLoading(false);
    }
  };

  const readyDocs = documents.filter((d) => d.status === 'ready');

  return (
    <div className="flex flex-col h-screen w-screen bg-surface-900 text-gray-100 overflow-hidden font-sans">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#16171B',
            color: '#F5F5F7',
            border: '1px solid #2B2D35',
            fontSize: '12px',
          },
        }}
      />

      {/* Top App Header */}
      <Header
        documentCount={readyDocs.length}
        activeDocCount={selectedDocIds.length}
        onNewChat={handleNewChat}
        onToggleMobileSidebar={() => setMobileSidebarOpen((prev) => !prev)}
      />

      {/* Main Workspace: Sidebar + Chat Window */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggleSelect={handleToggleSelectDoc}
          onSelectAll={handleSelectAllDocs}
          onDeselectAll={handleDeselectAllDocs}
          onDeleteDocument={handleDeleteDocument}
          onUploadFiles={handleUploadFiles}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
          onAskAboutDoc={handleAskAboutDoc}
          conversations={conversations}
          activeConvId={activeConvId}
          onSelectConversation={setActiveConvId}
          onDeleteConversation={handleDeleteConversation}
          onNewChat={handleNewChat}
          mobileOpen={mobileSidebarOpen}
          onCloseMobile={() => setMobileSidebarOpen(false)}
        />

        <main className="flex-1 overflow-hidden">
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            onClearChat={handleClearChat}
            suggestedQuestions={suggestedQuestions}
            totalReadyDocs={readyDocs.length}
            scopedCount={selectedDocIds.length}
          />
        </main>
      </div>
    </div>
  );
}

export default App;
