"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, MouseEvent as ReactMouseEvent } from "react";
import { MessageSquareMore, PanelRight, PanelRightClose } from "lucide-react";
import { useLocaleStore } from "@/lib/store/locale";
import { useTranslations } from "@/lib/i18n";
import Input from "@/components/common/Input";
import Button from "@/components/common/Button";
import { cn } from "@/lib/utils";
import { SimpleEditor } from "@/components/editor/markdownEditor/tiptap-templates/simple/simple-editor";

interface ChatMessage {
  id: string;
  role: "user" | "bot";
  text: string;
}

const createId = () =>
  typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

export default function WorkspacePage() {
  const { locale } = useLocaleStore();
  const t = useTranslations(locale);

  const [chatCollapsed, setChatCollapsed] = useState(false);
  const [chatWidthPx, setChatWidthPx] = useState(420);
  const [widthPreset, setWidthPreset] = useState<"roomy" | "compact" | null>("roomy");
  const [isDragging, setIsDragging] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");

  const dragState = useRef({ startX: 0, startWidth: 420 });

  useEffect(() => {
    if (!isDragging) {
      return;
    }

    const handlePointerMove = (event: MouseEvent) => {
      const delta = event.clientX - dragState.current.startX;
      const nextWidth = Math.min(560, Math.max(260, dragState.current.startWidth - delta));
      setWidthPreset(null);
      setChatWidthPx(nextWidth);
    };

    const handlePointerUp = () => {
      setIsDragging(false);
      document.body.style.userSelect = "";
    };

    window.addEventListener("mousemove", handlePointerMove);
    window.addEventListener("mouseup", handlePointerUp, { once: true });
    document.body.style.userSelect = "none";

    return () => {
      window.removeEventListener("mousemove", handlePointerMove);
      window.removeEventListener("mouseup", handlePointerUp);
      document.body.style.userSelect = "";
    };
  }, [isDragging]);

  const isSendDisabled = chatInput.trim().length === 0;
  const nextPresetLabel = widthPreset === "compact"
    ? t.workspace.chatPanel.roomy
    : widthPreset === "roomy"
      ? t.workspace.chatPanel.compact
      : t.workspace.chatPanel.roomy;

  const sidebarStyle = useMemo(
    () =>
      ({
        "--workspace-chat-width": chatCollapsed ? "3.5rem" : `${chatWidthPx}px`,
      }) as CSSProperties,
    [chatCollapsed, chatWidthPx]
  );

  const startDragging = (event: ReactMouseEvent<HTMLDivElement>) => {
    if (chatCollapsed) {
      return;
    }
    setIsDragging(true);
    dragState.current = { startX: event.clientX, startWidth: chatWidthPx };
  };

  const handlePresetToggle = () => {
    setWidthPreset((prev) => {
      const next = prev === "compact" ? "roomy" : prev === "roomy" ? "compact" : "roomy";
      setChatWidthPx(next === "roomy" ? 420 : 320);
      return next;
    });
  };

  const handleSendMessage = () => {
    if (isSendDisabled) {
      return;
    }

    const trimmed = chatInput.trim();
    const userMessage: ChatMessage = { id: createId(), role: "user", text: trimmed };
    const botMessage: ChatMessage = {
      id: createId(),
      role: "bot",
      text: `${t.workspace.chatPanel.thinking} ${trimmed}`.trim(),
    };

    setChatMessages((prev) => [...prev, userMessage, botMessage]);
    setChatInput("");
  };

  return (
    <div className="flex min-h-screen flex-col gap-6 bg-muted/20 p-6">
      <div className="space-y-2">
        <div className="flex items-center gap-3 text-primary">
          <PanelRight className="h-5 w-5" />
          <span className="text-sm font-medium uppercase tracking-wide">{t.workspace.title}</span>
        </div>
        <h1 className="text-3xl font-bold text-foreground">{t.workspace.subtitle}</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">{t.workspace.notice}</p>
      </div>

      <div className="flex flex-1 flex-col gap-6 xl:flex-row xl:gap-4">
        <section className="flex flex-1 flex-col rounded-3xl border border-border/60 bg-background/80 p-6 shadow-sm">
          <div className="flex flex-1 flex-col rounded-2xl border border-dashed border-border/50 bg-card/90 p-4">
            <div className="mx-auto flex w-full max-w-5xl flex-1">
              <SimpleEditor />
            </div>
          </div>
        </section>

        <div className="hidden xl:flex xl:w-4 xl:flex-none xl:items-stretch">
          <div
            className={cn(
              "mx-auto flex h-full w-1 cursor-col-resize items-center rounded-full",
              isDragging ? "bg-primary" : "bg-border/70"
            )}
            onMouseDown={startDragging}
          />
        </div>

        <aside
          style={sidebarStyle}
          className={cn(
            "relative flex w-full flex-col transition-[width] duration-200 xl:flex-none xl:w-(--workspace-chat-width)"
          )}
        >
          {!chatCollapsed && (
            <div
              className="absolute inset-y-0 left-0 hidden w-2 -translate-x-1/2 cursor-col-resize items-center xl:flex"
              onMouseDown={startDragging}
            >
              <div
                className={cn(
                  "mx-auto h-16 w-0.5 rounded-full",
                  isDragging ? "bg-primary" : "bg-border/70"
                )}
              />
            </div>
          )}
          {chatCollapsed ? (
            <div className="flex flex-1 items-start justify-end">
              <Button
                type="button"
                variant="ghost"
                className="flex items-center gap-2 rounded-full border border-border bg-background/80 px-4 py-2 text-sm font-medium text-foreground shadow-sm"
                onClick={() => setChatCollapsed(false)}
              >
                <PanelRightClose className="h-4 w-4" />
                <span className="hidden xl:inline">{t.workspace.chatPanel.expand}</span>
              </Button>
            </div>
          ) : (
            <div className="flex flex-1 flex-col rounded-3xl border border-border/70 bg-card/80 shadow-sm">
              <div className="flex items-start justify-between gap-3 border-b border-border/60 p-4">
                <div className="flex items-center gap-2">
                  <div className="rounded-full bg-primary/10 p-2 text-primary">
                    <MessageSquareMore className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-base font-semibold text-foreground">{t.workspace.chatPanel.title}</p>
                    <p className="text-xs text-muted-foreground">{t.workspace.chatPanel.description}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={handlePresetToggle}>
                        {nextPresetLabel}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setChatCollapsed(true)}>
                    {t.workspace.chatPanel.collapse}
                  </Button>
                </div>
              </div>

              <div className="flex flex-1 flex-col gap-4 p-4">
                <div className="flex-1 space-y-3 overflow-y-auto rounded-2xl border border-dashed border-border/60 bg-muted/30 p-4 text-sm">
                  {chatMessages.length === 0 ? (
                    <p className="text-muted-foreground">{t.workspace.chatPanel.empty}</p>
                  ) : (
                    chatMessages.map((message) => (
                      <div key={message.id} className="space-y-1">
                        <p className="text-xs uppercase tracking-wide text-muted-foreground">
                          {message.role === "user" ? "You" : "Bot"}
                        </p>
                        <p>{message.text}</p>
                      </div>
                    ))
                  )}
                </div>

                <div className="flex gap-2">
                  <Input
                    value={chatInput}
                    onChange={(event) => setChatInput(event.target.value)}
                    placeholder={t.workspace.chatPanel.inputPlaceholder}
                  />
                  <Button type="button" onClick={handleSendMessage} disabled={isSendDisabled}>
                    {t.workspace.chatPanel.send}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
