import axios from "axios";

const API = axios.create({
  baseURL: "https://opspilot-proj-production.up.railway.app/api",
});

export const uploadDocuments = async (files) => {
  const formData = new FormData();

  for (let file of files) {
    formData.append("files", file);
  }

  const response = await API.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

export const askQuestion = async (question) => {
  const response = await API.post("/chat", {
    question,
  });

  return response.data;
};