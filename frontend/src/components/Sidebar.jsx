import { FaRobot, FaFilePdf } from "react-icons/fa";

function Sidebar({ documents }) {
  return (
    <aside className="flex h-full flex-col bg-slate-900 text-white">
      {/* Logo */}
      <div className="border-b border-slate-800 p-6">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-600 p-3 shadow-lg">
            <FaRobot className="text-xl" />
          </div>

          <div>
            <h2 className="text-xl font-bold">OpsPilot</h2>
            <p className="text-xs text-slate-400">
              AI Document Assistant
            </p>
          </div>
        </div>
      </div>

      {/* Documents */}
      <div className="flex-1 overflow-y-auto p-5">
        <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">
          Uploaded Documents
        </p>

        {documents.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-700 bg-slate-800/40 p-6 text-center text-sm text-slate-400">
            No documents uploaded yet.
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc, index) => (
              <div
                key={index}
                className="flex items-center gap-3 rounded-xl bg-slate-800 p-3 transition-all duration-200 hover:bg-slate-700"
              >
                <FaFilePdf className="text-red-400" />

                <span className="truncate text-sm">
                  {doc}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-slate-800 p-4">
        <div className="rounded-xl bg-slate-800 p-3 text-center text-xs text-slate-400">
          Powered by FastAPI + LangChain + Groq
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;