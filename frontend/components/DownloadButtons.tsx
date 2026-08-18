"use client";

import { useState } from "react";
import {
  ProfileAnalysisResult,
  fetchMarkdownReport,
  downloadPdfReportBlob,
} from "../lib/api";
import { FileText, Download } from "lucide-react";

interface DownloadButtonsProps {
  username: string;
  result: ProfileAnalysisResult;
}

export default function DownloadButtons({
  username,
  result,
}: DownloadButtonsProps) {
  const [isDownloadingMd, setIsDownloadingMd] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  // Download Markdown Report
  const handleDownloadMarkdown = async () => {
    setIsDownloadingMd(true);
    try {
      const mdContent = await fetchMarkdownReport(username);
      const blob = new Blob([mdContent], {
        type: "text/markdown;charset=utf-8;",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${username}_github_audit.md`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Markdown download failed:", err);
      alert("Failed to download Markdown report.");
    } finally {
      setIsDownloadingMd(false);
    }
  };

  // Download WeasyPrint PDF Binary
  const handleDownloadPdf = async () => {
    setIsDownloadingPdf(true);
    try {
      const pdfBlob = await downloadPdfReportBlob(username);
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${username}_github_audit.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download failed:", err);
      alert("Failed to generate PDF report.");
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  return (
    <div className="flex flex-col gap-5 p-6 bg-neo-light dark:bg-neo-dark rounded-[2rem] shadow-neo-outset dark:shadow-neo-outset-dark print:hidden w-full">
      <div>
        <h3 className="text-xs font-bold tracking-wider text-gray-500 dark:text-gray-400 uppercase">
          Export Audit Report
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Save this developer evaluation as a Markdown document or rendered PDF.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-3 w-full">
        <button
          onClick={handleDownloadMarkdown}
          disabled={isDownloadingMd}
          className="flex-1 w-full px-4 py-3 bg-neo-light dark:bg-neo-dark hover:text-indigo-500 text-gray-700 dark:text-gray-200 text-xs font-bold rounded-xl transition-all shadow-neo-outset dark:shadow-neo-outset-dark active:shadow-neo-inset dark:active:shadow-neo-inset-dark flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
        >
          <FileText size={16} className="text-indigo-500" />
          {isDownloadingMd ? "Exporting..." : "Download Markdown"}
        </button>
        <button
          onClick={handleDownloadPdf}
          disabled={isDownloadingPdf}
          className="flex-1 w-full px-4 py-3 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-bold rounded-xl transition-all shadow-neo-outset dark:shadow-neo-outset-dark active:shadow-neo-inset dark:active:shadow-neo-inset-dark flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
        >
          <Download size={16} />
          {isDownloadingPdf ? "Generating PDF..." : "Download PDF"}
        </button>
      </div>
    </div>
  );
}
