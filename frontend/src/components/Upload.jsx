import { useRef, useState } from "react";
import { FiUploadCloud } from "react-icons/fi";
import { uploadDocuments } from "../services/api";

function Upload({ setDocuments }) {
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  const handleUpload = async (e) => {
    const files = Array.from(e.target.files);

    if (!files.length) return;

    try {
      setLoading(true);

      const data = await uploadDocuments(files);

      setDocuments(data.uploaded_files);

      alert("✅ Documents uploaded successfully!");
    } catch (err) {
      console.error(err);
      alert("Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-lg">
      <div className="flex flex-col items-center justify-center text-center">
        <div className="mb-5 rounded-full bg-blue-600/20 p-5">
          <FiUploadCloud className="text-5xl text-blue-400" />
        </div>

        <h2 className="text-xl font-semibold text-white">
          Upload your PDFs
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          Upload one or multiple PDF files and start chatting with them.
        </p>

        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleUpload}
          className="hidden"
        />

        <button
          onClick={() => inputRef.current.click()}
          disabled={loading}
          className="mt-6 rounded-xl bg-blue-600 px-6 py-3 font-medium transition hover:bg-blue-500 disabled:opacity-60"
        >
          {loading ? "Uploading..." : "Choose PDFs"}
        </button>
      </div>
    </div>
  );
}

export default Upload;