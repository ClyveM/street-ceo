package com.streetceo.app;

import android.Manifest;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.util.ArrayList;
import java.util.Locale;
import java.util.UUID;

/** Foreground speech only. The web controller owns wake framing and session restart. */
@CapacitorPlugin(name = "ApoSpeech", permissions = {@Permission(alias = "microphone", strings = {Manifest.permission.RECORD_AUDIO})})
public class ApoSpeechPlugin extends Plugin implements RecognitionListener {
    private SpeechRecognizer recognizer;
    private boolean active;
    private boolean foreground = true;
    private PluginCall permissionCall;
    private PluginCall resumeCall;
    private TextToSpeech speaker;
    private boolean speakerReady;
    private int speakerGeneration;
    private PluginCall speechCall;
    private String utteranceId;
    private final Handler outputTimer = new Handler(Looper.getMainLooper());
    private final Runnable outputTimeout = () -> { stopOutput(); };

    @PluginMethod public void start(PluginCall call) {
        getActivity().runOnUiThread(() -> {
            if (getPermissionState("microphone") != PermissionState.GRANTED) {
                if (permissionCall != null) { call.reject("Microphone permission is already being requested."); return; }
                permissionCall = call;
                requestPermissionForAlias("microphone", call, "microphonePermissionResult");
                return;
            }
            startGranted(call);
        });
    }
    @PermissionCallback private void microphonePermissionResult(PluginCall call) {
        if (permissionCall != call) return;
        permissionCall = null;
        if (getPermissionState("microphone") != PermissionState.GRANTED) {
            call.reject("Microphone permission denied. Allow Street CEO microphone access in Android Settings."); return;
        }
        getActivity().runOnUiThread(() -> startGranted(call));
    }
    private void startGranted(PluginCall call) {
            if (!foreground) { resumeCall = call; return; }
            if (!SpeechRecognizer.isRecognitionAvailable(getContext())) {
                call.reject("Android speech recognition is unavailable. Install or enable a speech recognition service."); return;
            }
            if (active) { call.reject("A speech session is already running."); return; }
            try {
                if (recognizer == null) {
                    recognizer = SpeechRecognizer.createSpeechRecognizer(getContext());
                    recognizer.setRecognitionListener(this);
                }
                Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, call.getString("language", "en-ZW"));
                intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
                intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
                active = true;
                recognizer.startListening(intent);
                call.resolve();
            } catch (Exception error) { active = false; call.reject("Could not start speech recognition: " + error.getMessage()); }
    }
    @PluginMethod public void stop(PluginCall call) {
        getActivity().runOnUiThread(() -> {
            if (permissionCall != null) { permissionCall.reject("Listening was stopped."); permissionCall = null; }
            if (resumeCall != null) { resumeCall.reject("Listening was stopped."); resumeCall = null; }
            release(); call.resolve();
        });
    }
    @PluginMethod public void speak(PluginCall call) {
        String text = call.getString("text", "").trim();
        if (text.isEmpty() || text.length() > 2000) { call.reject("Spoken response must contain 1 to 2000 characters."); return; }
        getActivity().runOnUiThread(() -> {
            if (!foreground) { call.reject("Spoken response paused while app is in the background."); return; }
            release();
            stopOutput();
            speechCall = call;
            utteranceId = UUID.randomUUID().toString();
            outputTimer.postDelayed(outputTimeout, 20000);
            if (speaker == null) {
                final int generation = ++speakerGeneration;
                speaker = new TextToSpeech(getContext(), status -> outputTimer.post(() -> {
                    if (generation != speakerGeneration || speaker == null) return;
                    if (status != TextToSpeech.SUCCESS) { failOutput("Android text to speech is unavailable."); if (speaker != null) speaker.shutdown(); speaker = null; speakerReady = false; return; }
                    speakerReady = true;
                    speaker.setLanguage(Locale.forLanguageTag("en-ZA"));
                    speaker.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                        @Override public void onStart(String id) {}
                        @Override public void onDone(String id) { finishOutput(id, null); }
                        @Override public void onError(String id) { finishOutput(id, "The spoken response could not play."); }
                    });
                    if (speechCall != null) playOutput();
                }));
            } else if (speakerReady) playOutput();
        });
    }
    private void playOutput() {
        if (speaker.speak(speechCall.getString("text", ""), TextToSpeech.QUEUE_FLUSH, null, utteranceId) == TextToSpeech.ERROR) failOutput("The spoken response could not play.");
    }
    private void finishOutput(String id, String error) {
        outputTimer.post(() -> {
            if (speechCall == null || id == null || !id.equals(utteranceId)) return;
            outputTimer.removeCallbacks(outputTimeout);
            PluginCall call = speechCall; speechCall = null; utteranceId = null;
            if (error == null) call.resolve(); else call.reject(error);
        });
    }
    private void failOutput(String error) {
        outputTimer.removeCallbacks(outputTimeout);
        if (speechCall != null) { speechCall.reject(error); speechCall = null; utteranceId = null; }
    }
    private void stopOutput() {
        if (speaker != null) speaker.stop();
        failOutput("Spoken response stopped.");
    }
    @PluginMethod public void stopSpeaking(PluginCall call) {
        getActivity().runOnUiThread(() -> { stopOutput(); call.resolve(); });
    }
    private void release() {
        active = false;
        if (recognizer != null) { recognizer.cancel(); recognizer.destroy(); recognizer = null; }
    }
    private void result(Bundle results, boolean isFinal) {
        if (!active) return;
        ArrayList<String> texts = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        if (isFinal) active = false;
        if (texts != null && !texts.isEmpty()) {
            JSObject event = new JSObject(); event.put("text", texts.get(0)); event.put("final", isFinal);
            notifyListeners("speech", event);
        }
        if (isFinal) notifyListeners("speechEnd", new JSObject());
    }
    @Override public void onResults(Bundle results) { result(results, true); }
    @Override public void onPartialResults(Bundle results) { result(results, false); }
    @Override public void onError(int code) {
        if (!active) return;
        active = false;
        JSObject event = new JSObject(); event.put("code", code);
        event.put("message", "Android speech recognition error " + code);
        notifyListeners("speechError", event);
        notifyListeners("speechEnd", new JSObject());
    }
    @Override protected void handleOnPause() { foreground = false; getActivity().runOnUiThread(() -> { release(); stopOutput(); notifyListeners("speechPaused", new JSObject()); }); }
    @Override protected void handleOnResume() {
        foreground = true;
        if (resumeCall != null) { PluginCall call = resumeCall; resumeCall = null; startGranted(call); }
        notifyListeners("speechResumed", new JSObject());
    }
    @Override protected void handleOnDestroy() { foreground = false; outputTimer.post(() -> {
        release(); stopOutput(); speakerGeneration++;
        if (permissionCall != null) { permissionCall.reject("App closed during permission request."); permissionCall = null; }
        if (resumeCall != null) { resumeCall.reject("App closed before listening resumed."); resumeCall = null; }
        if (speaker != null) { speaker.shutdown(); speaker = null; speakerReady = false; }
    }); }
    @Override public void onReadyForSpeech(Bundle params) { if (active) notifyListeners("speechReady", new JSObject()); }
    @Override public void onBeginningOfSpeech() {}
    @Override public void onRmsChanged(float rms) {}
    @Override public void onBufferReceived(byte[] buffer) {}
    @Override public void onEndOfSpeech() {}
    @Override public void onEvent(int type, Bundle params) {}
}

