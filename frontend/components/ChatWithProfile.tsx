"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { startChat, sendChatMessage } from "../lib/api";
import { Sparkles, Send, RotateCcw } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatWithProfileProps {
  username: string;
}

const SUGGESTED_QUESTIONS = [
  "What are their top technical skills?",
  "Summarize their most active repositories.",
  "How strong is their commit and project consistency?",
  "Would they be a good fit for a Full-Stack or Backend role?",
];

export default function ChatWithProfile({ username }: ChatWithProfileProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isInitializingSession, setIsInitializingSession] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Reference directly to the chat feed container to control scrollTop safely
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const prevMessageCountRef = useRef(0);

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  };

  // Only auto-scroll when a *new* message is added, ignoring initial load/reload hydration
  useEffect(() => {
    if (messages.length > prevMessageCountRef.current) {
      scrollToBottom();
    }
    prevMessageCountRef.current = messages.length;
  }, [messages]);

  const initializeNewSession = async () => {
    setIsInitializingSession(true);
    try {
      const res = await startChat(username);
      setSessionId(res.session_id);
      localStorage.setItem(`chat_session_${username}`, res.session_id);
      return res.session_id;
    } catch (err: any) {
      console.error("Failed to initialize session:", err);
      return null;
    } finally {
      setIsInitializingSession(false);
    }
  };

  useEffect(() => {
    if (!username) return;

    const savedSessionId = localStorage.getItem(`chat_session_${username}`);
    const savedMessages = localStorage.getItem(`chat_messages_${username}`);

    if (savedMessages) {
      try {
        const parsedMsgs = JSON.parse(savedMessages);
        setMessages(parsedMsgs);
        prevMessageCountRef.current = parsedMsgs.length;
      } catch (e) {
        console.error("Failed to parse saved chat history:", e);
      }
    }

    if (savedSessionId) {
      setSessionId(savedSessionId);
    } else {
      initializeNewSession();
    }
  }, [username]);

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(
        `chat_messages_${username}`,
        JSON.stringify(messages),
      );
    }
  }, [messages, sessionId, username]);

  const handleResetChat = () => {
    localStorage.removeItem(`chat_session_${username}`);
    localStorage.removeItem(`chat_messages_${username}`);
    setMessages([]);
    prevMessageCountRef.current = 0;
    initializeNewSession();
  };

  const handleSend = async (questionText?: string) => {
    let currentSessionId = sessionId;
    const query = (questionText || input).trim();
    if (!query || isLoading) return;

    // If session is missing entirely, try to spin one up on the fly before sending
    if (!currentSessionId) {
      currentSessionId = await initializeNewSession();
      if (!currentSessionId) {
        setMessages((prev) => [
          ...prev,
          { role: "user", content: query },
          {
            role: "assistant",
            content:
              "Failed to establish a chat session with the backend. Please try again.",
          },
        ]);
        return;
      }
    }

    setInput("");
    const updatedMessages: Message[] = [
      ...messages,
      { role: "user", content: query },
    ];
    setMessages(updatedMessages);
    setIsLoading(true);

    try {
      const responseText = await sendChatMessage(currentSessionId, query);
      const finalMsgs: Message[] = [
        ...updatedMessages,
        { role: "assistant", content: responseText },
      ];
      setMessages(finalMsgs);
    } catch (err: any) {
      const errorMessage = err?.message || "";

      // AUTO-HEAL: If session expired/not found, automatically reset and retry once!
      if (
        errorMessage.toLowerCase().includes("expired") ||
        errorMessage.toLowerCase().includes("not found")
      ) {
        localStorage.removeItem(`chat_session_${username}`);
        const freshSessionId = await initializeNewSession();

        if (freshSessionId) {
          try {
            const retryResponse = await sendChatMessage(freshSessionId, query);
            setMessages([
              ...updatedMessages,
              { role: "assistant", content: retryResponse },
            ]);
            setIsLoading(false);
            return;
          } catch (retryErr: any) {
            // Fallthrough to standard error display if retry fails
          }
        }
      }

      setMessages([
        ...updatedMessages,
        {
          role: "assistant",
          content:
            errorMessage ||
            "Sorry, I failed to process that question. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const askedQuestions = messages
    .filter((m) => m.role === "user")
    .map((m) => m.content);

  const availableQuestions = SUGGESTED_QUESTIONS.filter(
    (q) => !askedQuestions.includes(q),
  );

  const isChatDisabled = isLoading || isInitializingSession;

  return (
    <div className="p-6 bg-neo-light dark:bg-neo-dark rounded-[2rem] shadow-neo-outset dark:shadow-neo-outset-dark space-y-5 w-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark text-indigo-500">
            <Sparkles size={16} />
          </div>
          <div>
            <h2 className="text-[10px] font-bold tracking-wider text-gray-400 uppercase">
              AI Assistant
            </h2>
            <p className="text-xs font-bold text-gray-800 dark:text-white">
              Ask questions about @{username}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleResetChat}
            disabled={isLoading}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-indigo-500 bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark active:shadow-neo-inset dark:active:shadow-neo-inset-dark rounded-xl transition-all cursor-pointer disabled:opacity-50"
            title="Clear chat history and start fresh"
          >
            <RotateCcw size={14} />
          </button>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark text-[10px] font-bold text-indigo-500">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            {sessionId && !isInitializingSession ? "Active" : "Init..."}
          </div>
        </div>
      </div>

      {/* Suggested Quick Questions */}
      {availableQuestions.length > 0 && (
        <div className="flex flex-col gap-2">
          {availableQuestions.map((q) => (
            <button
              key={q}
              onClick={() => handleSend(q)}
              disabled={isChatDisabled}
              className="text-xs px-4 py-2.5 bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark hover:shadow-neo-inset dark:hover:shadow-neo-inset-dark text-gray-600 dark:text-gray-300 hover:text-indigo-500 rounded-xl transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer font-medium"
            >
              💡 {q}
            </button>
          ))}
        </div>
      )}

      {/* Chat Feed Container with ref */}
      <div
        ref={chatContainerRef}
        className="p-4 bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark rounded-2xl space-y-3 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-400 dark:scrollbar-thumb-gray-700"
      >
        {messages.length === 0 && !isInitializingSession && (
          <div className="text-center py-6 text-xs text-gray-400 font-medium">
            Select a question above or type below to start chatting with @
            {username}&apos;s profile context.
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[85%] px-4 py-3 rounded-2xl text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-indigo-500 text-white rounded-br-none shadow-md"
                  : "bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark text-gray-700 dark:text-gray-200 rounded-bl-none"
              }`}
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => (
                    <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc pl-4 mb-2 space-y-1 my-1">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal pl-4 mb-2 space-y-1 my-1">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => <li className="text-xs">{children}</li>,
                  h1: ({ children }) => (
                    <h1 className="text-sm font-bold mb-2 border-b border-gray-300 dark:border-gray-700 pb-1 mt-1">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xs font-bold text-indigo-400 mb-1.5 mt-2 uppercase tracking-wide">
                      {children}
                    </h2>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-bold">{children}</strong>
                  ),
                  code: ({ children }) => (
                    <code className="bg-gray-200 dark:bg-gray-900 text-indigo-500 px-1.5 py-0.5 rounded text-[11px] font-mono">
                      {children}
                    </code>
                  ),
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}

        {(isLoading || isInitializingSession) && (
          <div className="flex justify-start">
            <div className="bg-neo-light dark:bg-neo-dark shadow-neo-outset dark:shadow-neo-outset-dark text-gray-400 px-4 py-2.5 rounded-2xl rounded-bl-none text-xs flex items-center gap-2">
              <span className="w-2 h-2 bg-indigo-500 rounded-full animate-ping" />
              {isInitializingSession
                ? "Starting session..."
                : "Analyzing profile context..."}
            </div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            isInitializingSession
              ? "Connecting session..."
              : `Ask anything about @${username}...`
          }
          disabled={isChatDisabled}
          className="flex-1 px-4 py-3 bg-neo-light dark:bg-neo-dark shadow-neo-inset dark:shadow-neo-inset-dark rounded-xl text-xs font-medium text-gray-800 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          type="submit"
          disabled={isChatDisabled || !input.trim()}
          className="px-4 py-3 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-bold rounded-xl transition-all shadow-neo-outset dark:shadow-neo-outset-dark active:shadow-neo-inset dark:active:shadow-neo-inset-dark disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center cursor-pointer"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
