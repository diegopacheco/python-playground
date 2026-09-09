import posthog from "posthog-js";

declare const __POSTHOG_KEY__: string;
declare const __POSTHOG_HOST__: string;

let started = false;

export function startAnalytics(): boolean {
  if (started) return true;
  if (!__POSTHOG_KEY__ || !__POSTHOG_HOST__) return false;

  posthog.init(__POSTHOG_KEY__, {
    api_host: __POSTHOG_HOST__,
    defaults: "2025-05-24",
    capture_pageview: true,
    capture_pageleave: true,
    person_profiles: "always",
    disable_session_recording: false,
    session_recording: {
      maskAllInputs: true,
    },
    loaded: (client) => {
      client.startSessionRecording();
      client.capture("$pageview");
      client.capture("ui_loaded", { surface: "web" });
    },
  });
  started = true;
  return true;
}

export function identifyUser(userId: string): void {
  if (!started || !userId) return;
  posthog.identify(userId);
}

export type ReplayState = {
  recording: boolean;
  replay: string | null;
  sessionId: string | null;
};

export function replayState(): ReplayState {
  if (!started) return { recording: false, replay: null, sessionId: null };
  return {
    recording: Boolean(posthog.sessionRecordingStarted?.()),
    replay: posthog.get_session_replay_url?.({ withTimestamp: true }) ?? null,
    sessionId: posthog.get_session_id?.() ?? null,
  };
}
