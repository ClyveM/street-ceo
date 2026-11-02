package com.streetceo.app;

import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;

import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private View counterContent;
    private boolean keyboardVisible;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        registerPlugin(ApoSpeechPlugin.class);
        super.onCreate(savedInstanceState);
        // ApoSpeech requests permission when foreground listening starts.
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        counterContent = findViewById(android.R.id.content);
        // Capacitor 7 may install automatic Android 15 WebView margins. The
        // outer content container owns these instead, including hidden bars.
        View webView = getBridge().getWebView();
        ViewCompat.setOnApplyWindowInsetsListener(webView, null);
        ViewGroup.LayoutParams webParams = webView.getLayoutParams();
        if (webParams instanceof ViewGroup.MarginLayoutParams) {
            ((ViewGroup.MarginLayoutParams) webParams).setMargins(0, 0, 0, 0);
            webView.setLayoutParams(webParams);
        }
        ViewCompat.setOnApplyWindowInsetsListener(counterContent, (view, windowInsets) -> {
            // Transient bars overlay content. Reserve their stable area even while
            // hidden, including side navigation in landscape; never add it twice.
            Insets bars = windowInsets.getInsetsIgnoringVisibility(
                WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.displayCutout());
            Insets ime = windowInsets.getInsets(WindowInsetsCompat.Type.ime());
            view.setPadding(bars.left, bars.top, bars.right, Math.max(bars.bottom, ime.bottom));
            boolean wasKeyboardVisible = keyboardVisible;
            keyboardVisible = windowInsets.isVisible(WindowInsetsCompat.Type.ime());
            if (wasKeyboardVisible && !keyboardVisible) view.post(this::hideCounterNavigation);
            // This container owns the insets; WebView gets the already safe viewport.
            return WindowInsetsCompat.CONSUMED;
        });
        ViewCompat.requestApplyInsets(counterContent);
        counterContent.post(this::hideCounterNavigation);
    }

    private void hideCounterNavigation() {
        if (counterContent == null || !hasWindowFocus() || keyboardVisible || isFinishing() || isDestroyed()) return;
        WindowInsetsControllerCompat controller = WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        controller.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
        controller.hide(WindowInsetsCompat.Type.navigationBars());
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus && counterContent != null) counterContent.post(this::hideCounterNavigation);
    }

    @Override
    public void onResume() {
        super.onResume();
        if (counterContent != null) {
            ViewCompat.requestApplyInsets(counterContent);
            counterContent.post(this::hideCounterNavigation);
        }
    }
}

