import { useEffect, useRef, useState } from "react";
import { FiSend } from "react-icons/fi";
import { askQuestion } from "../services/api";

function Chat() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleAsk = async () => {
    if (!question.trim() || loading) return;

    const userMessage = {
      role: "user",
      text: question,
    };

    setMessages((prev) => [...prev, userMessage]);

    const currentQuestion = question;
    setQuestion("");
    setLoading(true);

    try {
      const data = await askQuestion(currentQuestion);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
        },
      ]);
    } catch (err) {
      console.error(err);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Something went wrong while generating the answer.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col">

      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-slate-500">
            Ask anything about your uploaded PDFs.
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            className={`max-w-3xl rounded-2xl px-5 py-4 ${
              msg.role === "user"
                ? "ml-auto bg-blue-600 text-white"
                : "bg-slate-800 text-slate-100"
            }`}
          >
            {msg.text}
          </div>
        ))}

        {loading && (
          <div className="max-w-md rounded-2xl bg-slate-800 px-5 py-4 text-slate-300">
            Thinking...
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="border-t border-slate-800 p-5">
        <div className="flex items-center gap-3">

          <textarea
            rows={2}
            value={question}
            placeholder="Ask anything about your documents..."
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleAsk();
              }
            }}
            className="flex-1 resize-none rounded-xl border border-slate-700 bg-slate-900 p-4 text-white outline-none focus:border-blue-500"
          />

          <button
            onClick={handleAsk}
            disabled={loading}
            className="rounded-xl bg-blue-600 p-4 transition hover:bg-blue-500 disabled:opacity-50"
          >
            <FiSend />
          </button>

        </div>
      </div>
    </div>
  );
}

export default Chat;