"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";

import { Button, Chip } from "@/components/ui";
import { api, type ChatMessage, type GuardData, type KbSheet } from "@/lib/api";

import { LoadingBlock, ScreenHeader, Sheet, useApiData, useRequireAuth } from "./shared";

export function ChatListScreen() {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const { data, error, loading, reload } = useApiData(() => api.conversations(), ready);

  if (!ready || loading || !data) return <LoadingBlock error={error} reload={reload} />;

  return (
    <div style={{ paddingBottom: 24 }}>
      <ScreenHeader title={t("conversation.listTitle")} />
      <div className="px">
        {data.length === 0 ? (
          <div className="list-empty">{t("conversation.empty")}</div>
        ) : (
          data.map((conversation) => (
            <button
              key={conversation.id}
              className="post"
              onClick={() => router.push(`/chat/${conversation.id}`)}
              type="button"
            >
              <div className="post__top">
                <Chip tone="neutral">{t(`done.statusChip.${conversation.status}` as never)}</Chip>
                {conversation.translation_on ? (
                  <Chip tone="warning">{t("conversation.translationOn")}</Chip>
                ) : null}
              </div>
              <div className="post__title">{conversation.title}</div>
              <div className="post__meta">
                {t("conversation.membersMeta", {
                  count: conversation.member_count,
                  cities: conversation.member_cities
                    .map((city) => t(`cities.${city}` as never))
                    .join(", "),
                })}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

function LevelDots({ level }: { level: string }) {
  const filled = level === "STRONG" ? 3 : level === "MODERATE" ? 2 : 1;
  return (
    <>
      {[1, 2, 3].map((index) => (
        <i key={index} data-filled={index <= filled} />
      ))}
    </>
  );
}

function HelpPanel({
  help,
  onWhy,
}: {
  help: NonNullable<ChatMessage["help"]>;
  onWhy: (kbId: string) => void;
}) {
  const t = useTranslations("conversation");
  return (
    <div className="help">
      <div className="help__head">
        <span aria-hidden>💡</span>
        <b>{help.heading === "MAY_MEAN" ? t("headingMayMean") : t("headingReadAs")}</b>
        <span className="help__level">
          <LevelDots level={help.level} />
          <span>
            {help.level === "STRONG"
              ? t("levelStrong")
              : help.level === "MODERATE"
                ? t("levelModerate")
                : t("levelReference")}
          </span>
        </span>
      </div>
      <div className="help__text">{help.annotation}</div>
      {help.kb_ids[0] ? (
        <button className="help__why" onClick={() => onWhy(help.kb_ids[0])} type="button">
          {t("helpWhy")}
        </button>
      ) : null}
    </div>
  );
}

function MessageBubble({
  message,
  onWhy,
}: {
  message: ChatMessage;
  onWhy: (kbId: string) => void;
}) {
  const t = useTranslations();
  return (
    <>
      <div className={message.mine ? "msg msg--me" : "msg msg--you"}>
        <div className="msg__who">
          {message.mine ? (
            <>
              <span>{t("common.me")}</span>
              {message.translation_status === "REVIEW_REQUIRED" ? (
                <Chip tone="warning">{t("conversation.reviewChip")}</Chip>
              ) : null}
              {message.guard_badge === "CHECK_PASSED" ? (
                <Chip tone="verified">{t("conversation.guardPassed")}</Chip>
              ) : message.guard_badge === "SENT_UNCHANGED" ? (
                <Chip tone="warning">{t("conversation.guardUnchanged")}</Chip>
              ) : null}
            </>
          ) : (
            <>
              <span>{message.sender.name}</span>
              <span>{message.sender.locale.toUpperCase()}</span>
              {message.translation_status === "REVIEW_REQUIRED" ? (
                <Chip tone="warning">{t("conversation.reviewChip")}</Chip>
              ) : null}
            </>
          )}
        </div>
        <div className="bub">
          {message.shown_text}
          {message.mine ? (
            message.translation_status === "REVIEW_REQUIRED" ? (
              <div className="bub__origin">{t("conversation.slangNote")}</div>
            ) : message.receipts.length > 0 ? (
              <div className="bub__origin">
                {t("conversation.receivedAs", { name: message.receipts[0].name })}
                <br />
                {message.receipts[0].text}
              </div>
            ) : null
          ) : message.original_line ? (
            <div className="bub__origin">
              {t("conversation.origin", { text: message.original_line })}
            </div>
          ) : null}
        </div>
      </div>
      {!message.mine && message.help ? <HelpPanel help={message.help} onWhy={onWhy} /> : null}
    </>
  );
}

function KbEvidenceSheet({ kbId, onClose }: { kbId: string | null; onClose: () => void }) {
  const t = useTranslations("conversation");
  const [sheet, setSheet] = useState<KbSheet | null>(null);
  const [dispute, setDispute] = useState("");
  const [disputeDone, setDisputeDone] = useState(false);
  useEffect(() => {
    setSheet(null);
    setDispute("");
    setDisputeDone(false);
    if (kbId)
      api
        .kb(kbId)
        .then(setSheet)
        .catch(() => null);
  }, [kbId]);
  return (
    <Sheet onClose={onClose} open={kbId !== null} subtitle={kbId ?? ""} title={t("kbTitle")}>
      {sheet ? (
        <>
          <div className="kv">
            <span>{t("kbClaim")}</span>
            <span>{sheet.claim}</span>
          </div>
          <div className="kv">
            <span>{t("kbLocale")}</span>
            <span className="cc">{sheet.scope_locale.toUpperCase()}</span>
          </div>
          <div className="kv">
            <span>{t("kbContext")}</span>
            <span>{sheet.scope_context}</span>
          </div>
          <div className="kv">
            <span>{t("kbVerified")}</span>
            <span className="mono">{sheet.verified_at}</span>
          </div>
          <div className="kv">
            <span>{t("kbConfidence")}</span>
            <span className="mono">
              {t("kbBase", { value: sheet.base_confidence.toFixed(2) })} ·{" "}
              {t("kbEffective", { value: sheet.effective_confidence.toFixed(2) })} ·{" "}
              {t("kbDisputes", { count: sheet.dispute_count })}
            </span>
          </div>
          <div className="kv" style={{ borderBottom: 0 }}>
            <span>{t("kbSources")}</span>
            <span>
              {sheet.sources.map((source) => (
                <span key={source.url} style={{ display: "block" }}>
                  {source.title}
                </span>
              ))}
            </span>
          </div>
          {disputeDone ? (
            <div className="check__fix" style={{ marginTop: 12 }}>
              {t("kbDisputeDone")}
            </div>
          ) : (
            <>
              <div className="field">
                <label htmlFor="kb-dispute">{t("kbDispute")}</label>
                <input
                  id="kb-dispute"
                  onChange={(event) => setDispute(event.target.value)}
                  placeholder={t("kbDisputePlaceholder")}
                  value={dispute}
                />
              </div>
              <div style={{ marginTop: 12 }}>
                <Button
                  disabled={!dispute.trim()}
                  onClick={async () => {
                    const updated = await api.disputeKb(sheet.id, dispute.trim());
                    setSheet(updated);
                    setDisputeDone(true);
                  }}
                  size="small"
                  type="button"
                  variant="ghost"
                >
                  {t("kbDispute")}
                </Button>
              </div>
            </>
          )}
        </>
      ) : null}
    </Sheet>
  );
}

export function ChatScreen({ conversationId }: { conversationId: string }) {
  const ready = useRequireAuth();
  const t = useTranslations();
  const router = useRouter();
  const [input, setInput] = useState("");
  const [guard, setGuard] = useState<GuardData | null>(null);
  const [sending, setSending] = useState(false);
  const [kbId, setKbId] = useState<string | null>(null);
  const guardTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scrollAnchor = useRef<HTMLDivElement | null>(null);
  const summaryQuery = useApiData(() => api.conversation(conversationId), ready);
  const messagesQuery = useApiData<ChatMessage[]>(() => api.messages(conversationId), ready);

  // Light polling keeps the crew chat fresh without websockets (local demo).
  useEffect(() => {
    if (!ready) return;
    const interval = setInterval(() => messagesQuery.reload(), 5000);
    return () => clearInterval(interval);
  }, [ready, messagesQuery.reload]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    scrollAnchor.current?.scrollIntoView({ block: "end" });
  }, [messagesQuery.data?.length]);

  // Pre-compute the guard after 400ms of typing silence (§7.6) so the panel
  // is instant when the user hits send.
  useEffect(() => {
    if (!ready) return;
    if (guardTimer.current) clearTimeout(guardTimer.current);
    if (input.trim().length < 2) {
      setGuard(null);
      return;
    }
    guardTimer.current = setTimeout(async () => {
      try {
        const envelope = await api.guard(conversationId, input);
        setGuard(envelope.data.display ? envelope.data : null);
      } catch {
        setGuard(null);
      }
    }, 400);
    return () => {
      if (guardTimer.current) clearTimeout(guardTimer.current);
    };
  }, [input, conversationId, ready]);

  const send = useCallback(
    async (choice: "ORIGINAL" | "SUGGESTION" | null) => {
      const text = choice === "SUGGESTION" && guard?.rewritten_text ? guard.rewritten_text : input;
      if (!text.trim() || sending) return;
      setSending(true);
      try {
        let guardToken = choice && guard ? guard.guard_token : undefined;
        // A suggestion is different text — fetch its token before sending.
        if (choice === "SUGGESTION") {
          const check = await api.guard(conversationId, text);
          guardToken = check.data.guard_token;
        }
        await api.sendMessage(conversationId, {
          client_message_id: `w-${Date.now()}-${Math.floor(Math.random() * 1e6)}`,
          text,
          guard_token: guardToken,
          guard_choice: choice ?? undefined,
        });
        setInput("");
        setGuard(null);
        messagesQuery.reload();
      } catch (err) {
        const details = (err as { details?: GuardData }).details;
        if (details?.guard_token) setGuard(details);
      } finally {
        setSending(false);
      }
    },
    [conversationId, guard, input, sending, messagesQuery],
  );

  if (!ready || messagesQuery.loading || !messagesQuery.data) {
    return <LoadingBlock error={messagesQuery.error} reload={messagesQuery.reload} />;
  }

  const summary = summaryQuery.data;
  const messages = messagesQuery.data;

  return (
    <div style={{ paddingBottom: 150 }}>
      <ScreenHeader
        onBack={() => router.push("/chat")}
        subtitle={
          summary
            ? t("conversation.membersMeta", {
                count: summary.member_count,
                cities: summary.member_cities
                  .map((city) => t(`cities.${city}` as never))
                  .join(", "),
              })
            : undefined
        }
        title={summary?.title ?? ""}
        trailing={
          summary?.translation_on ? (
            <Chip tone="warning">{t("conversation.translationOn")}</Chip>
          ) : null
        }
      />
      <div className="chat-scroll">
        {summary ? (
          <>
            <div className="sys">{t("conversation.sysCrew", { count: summary.member_count })}</div>
            <div className="sys sys--info">
              <b>{t("conversation.sysLangBold")}</b> {t("conversation.sysLangRest")}
            </div>
          </>
        ) : null}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} onWhy={setKbId} />
        ))}
        <div ref={scrollAnchor} />
      </div>

      <div className="chat-dock">
        <div className="chat-dock__inner">
          {guard?.display ? (
            <div className={guard.risk === "HIGH" ? "check" : "check check--soft"}>
              <div className="check__head">
                <span aria-hidden>✋</span>
                <span>{t("conversation.checkTitle")}</span>
              </div>
              <div className="check__text">{guard.reader_reading}</div>
              {guard.suggestion ? (
                <div className="check__fix">
                  <small>{t("conversation.checkFix")}</small>
                  {guard.suggestion}
                </div>
              ) : null}
              <div className="pair" style={{ marginTop: 12 }}>
                <Button
                  disabled={sending}
                  onClick={() => send("ORIGINAL")}
                  size="small"
                  type="button"
                  variant="ghost"
                >
                  {t("conversation.sendOriginal")}
                </Button>
                {guard.rewritten_text ? (
                  <Button
                    disabled={sending}
                    onClick={() => send("SUGGESTION")}
                    size="small"
                    type="button"
                  >
                    {t("conversation.sendSuggestion")}
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}
          <div className="composer">
            <input
              aria-label={t("conversation.composerPlaceholder")}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !guard?.display) send(null);
              }}
              placeholder={t("conversation.composerPlaceholder")}
              value={input}
            />
            <button
              aria-label={t("common.send")}
              disabled={sending || !input.trim()}
              onClick={() => (guard?.display ? undefined : send(null))}
              type="button"
            >
              ↑
            </button>
          </div>
        </div>
      </div>

      <KbEvidenceSheet kbId={kbId} onClose={() => setKbId(null)} />
    </div>
  );
}
