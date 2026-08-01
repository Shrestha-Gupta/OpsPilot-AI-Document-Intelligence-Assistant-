import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Upload from "./components/Upload";
import Chat from "./components/Chat";

function App() {
  const [documents, setDocuments] = useState([]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="w-72 border-r border-slate-800 bg-slate-900">
        <Sidebar documents={documents} />
      </aside>

      {/* Main Content */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b border-slate-800 bg-slate-900/60 px-8 py-5 backdrop-blur">
          <h1 className="text-3xl font-bold tracking-tight">
            🚀 OpsPilot
          </h1>

          <p className="mt-1 text-sm text-slate-400">
            AI-powered Document Intelligence Assistant
          </p>
        </header>

        {/* Body */}
        <div className="flex flex-1 flex-col gap-6 overflow-hidden p-8">
          <Upload setDocuments={setDocuments} />

          <div className="flex-1 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-xl">
            <Chat />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;