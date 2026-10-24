package xyz.tiresia.olam;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.ShortcutInfo;
import android.content.pm.ShortcutManager;
import android.graphics.Insets;
import android.graphics.drawable.Icon;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.webkit.CookieManager;
import android.webkit.RenderProcessGoneDetail;
import android.webkit.SslErrorHandler;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import android.window.OnBackInvokedCallback;
import android.window.OnBackInvokedDispatcher;

import java.util.List;

/**
 * Olam: the server's page in a WebView, between the status bar and the navigation bar (or the
 * keyboard). The page is the whole interface. Before there's a server, and from Server on the
 * icon's long-press, the window is the choice of server instead: the public demo or your own.
 *
 * Only the server's own pages load here: other sites go to the browser, obsidian:// to Obsidian.
 * Back goes back in the page first, and leaves only when there's nowhere to go.
 */
public class MainActivity extends Activity {
    static final String ACTION_SERVER = "xyz.tiresia.olam.SERVER";

    private WebView web;
    private View chooser, offline, problem;
    private EditText address;
    private String loaded;                  // the server the page came from
    private String failedUrl;               // the page that didn't come, while the no-answer screen is up
    private boolean forget;                 // the history before the page goes, once it's there
    private Object backCallback;            // an OnBackInvokedCallback, registered while Back has somewhere to go
    private boolean backRegistered;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        if ((getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0) WebView.setWebContentsDebuggingEnabled(true);
        setContentView(R.layout.main);
        web = findViewById(R.id.web);
        chooser = findViewById(R.id.chooser);
        offline = findViewById(R.id.offline);
        problem = findViewById(R.id.problem);
        address = findViewById(R.id.address);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);                  // the demo keeps your progress in the page's storage
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setUserAgentString(s.getUserAgentString() + " Olam/" + version() + " (Android shell)");
        CookieManager.getInstance().setAcceptCookie(true);   // the sign-in, kept for its year
        web.setBackgroundColor(getColor(R.color.ground));
        web.setWebViewClient(new Pages());

        ((TextView) findViewById(R.id.demoServer)).setText(Server.label(Server.DEMO));
        findViewById(R.id.demo).setOnClickListener(v -> choose(Server.DEMO));
        findViewById(R.id.open).setOnClickListener(v -> chooseTyped());
        address.setOnEditorActionListener((v, action, e) -> {
            if (action != EditorInfo.IME_ACTION_GO && e == null) return false;
            chooseTyped();
            return true;
        });
        findViewById(R.id.retry).setOnClickListener(v -> {
            if (web.getUrl() == null) { open(); return; }
            failedUrl = null;
            web.reload();
        });
        findViewById(R.id.change).setOnClickListener(v -> showChooser());

        window();
        shortcut();
        if (Server.base(this) != null) open();
        if (Server.base(this) == null || ACTION_SERVER.equals(getIntent().getAction())) showChooser();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (ACTION_SERVER.equals(intent.getAction())) showChooser();
    }

    /** The server's first page, and none of the last server's history behind it. */
    private void open() {
        loaded = Server.base(this);
        forget = true;
        failedUrl = null;
        offline.setVisibility(View.GONE);
        web.loadUrl(loaded);
    }

    // ---- the choice of server ----

    private void showChooser() {
        String base = Server.base(this);
        address.setText(base == null || base.equals(Server.DEMO) ? "" : base);
        problem.setVisibility(View.GONE);
        chooser.setVisibility(View.VISIBLE);
        chooser.scrollTo(0, 0);
        findViewById(R.id.column).requestFocus();
        updateBack();
    }

    private void hideChooser() {
        getSystemService(InputMethodManager.class).hideSoftInputFromWindow(address.getWindowToken(), 0);
        chooser.setVisibility(View.GONE);
        updateBack();
    }

    private void chooseTyped() {
        String base = Server.normalize(address.getText().toString());
        if (base == null) {
            problem.setVisibility(address.getText().toString().trim().isEmpty() ? View.GONE : View.VISIBLE);
            return;
        }
        choose(base);
    }

    private void choose(String base) {
        Server.setBase(this, base);
        hideChooser();
        if (!base.equals(loaded) || failedUrl != null) open();
    }

    /** Server, on the icon's long-press. */
    private void shortcut() {
        ShortcutManager m = getSystemService(ShortcutManager.class);
        if (m == null) return;
        ShortcutInfo server = new ShortcutInfo.Builder(this, "server")
                .setShortLabel(getString(R.string.server))
                .setIcon(Icon.createWithResource(this, R.drawable.ic_shortcut_server))
                .setIntent(new Intent(this, MainActivity.class).setAction(ACTION_SERVER))
                .build();
        try {
            m.setDynamicShortcuts(List.of(server));
        } catch (IllegalStateException e) {
            // the launcher's rate limit; the shortcut is already there from an earlier start
        }
    }

    // ---- Back ----

    /** The chooser closes (when there's a server to go back to), then the page goes back; with
     *  nowhere to go, Back is the system's, and leaves. */
    private boolean backHere() {
        if (chooser.getVisibility() == View.VISIBLE) return Server.base(this) != null && loaded != null;
        return web.canGoBack();
    }

    private void back() {
        if (chooser.getVisibility() == View.VISIBLE) {
            if (Server.base(this) != null && loaded != null) hideChooser();
            else moveTaskToBack(true);
        } else if (web.canGoBack()) {
            web.goBack();
        } else {
            moveTaskToBack(true);
        }
    }

    /** From Android 13 Back is a callback, there only while the app has a use for it, so the
     *  system's own Back (and its preview of where it goes) works the rest of the time. */
    private void updateBack() {
        if (Build.VERSION.SDK_INT < 33) return;
        boolean want = backHere();
        if (want == backRegistered) return;
        if (backCallback == null) backCallback = (OnBackInvokedCallback) this::back;
        OnBackInvokedDispatcher d = getOnBackInvokedDispatcher();
        if (want) d.registerOnBackInvokedCallback(OnBackInvokedDispatcher.PRIORITY_DEFAULT, (OnBackInvokedCallback) backCallback);
        else d.unregisterOnBackInvokedCallback((OnBackInvokedCallback) backCallback);
        backRegistered = want;
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (backHere()) back();
        else super.onBackPressed();
    }

    // ---- the window ----

    /** Edge to edge, with the content padded by hand: the page sits between the status bar and
     *  the navigation bar, or the keyboard when it's open (so the page's bottom stays on screen).
     *  The ground shows behind the bars, with light icons on it. */
    @SuppressWarnings("deprecation")
    private void window() {
        // from Android 15 every window is edge to edge; before it, this window asks to be
        if (Build.VERSION.SDK_INT < 35) getWindow().setDecorFitsSystemWindows(false);
        getWindow().getDecorView().setBackgroundColor(getColor(R.color.ground));
        View content = findViewById(android.R.id.content);
        content.setOnApplyWindowInsetsListener((v, in) -> {
            Insets bars = in.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            int ime = in.getInsets(WindowInsets.Type.ime()).bottom;
            v.setPadding(bars.left, bars.top, bars.right, Math.max(bars.bottom, ime));
            return WindowInsets.CONSUMED;
        });
        WindowInsetsController c = getWindow().getInsetsController();
        int light = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
        if (c != null) c.setSystemBarsAppearance(0, light);
        // on a tablet, the chooser and the no-answer screen keep to a column
        View root = findViewById(R.id.root), column = findViewById(R.id.column);
        root.addOnLayoutChangeListener((v, l, t, r, b, ol, ot, or, ob) -> {
            int side = Math.max(dp(24), (r - l - dp(440)) / 2);
            for (View p : new View[]{column, offline}) {
                if (p.getPaddingLeft() != side) p.setPadding(side, p.getPaddingTop(), side, p.getPaddingBottom());
            }
        });
    }

    private int dp(int n) {
        return Math.round(n * getResources().getDisplayMetrics().density);
    }

    private String version() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "?";
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        CookieManager.getInstance().flush();
    }

    @Override
    protected void onDestroy() {
        if (web != null) web.destroy();
        super.onDestroy();
    }

    /** Anything that isn't the server's: the browser, Obsidian, Mail. */
    private void outside(Uri url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, url).addCategory(Intent.CATEGORY_BROWSABLE)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, "obsidian".equalsIgnoreCase(url.getScheme()) ? R.string.noObsidian : R.string.noApp,
                    Toast.LENGTH_SHORT).show();
        }
    }

    /** No answer from the server: its address, Try again, and Server. */
    private void noAnswer(Uri url) {
        failedUrl = url.toString();
        ((TextView) findViewById(R.id.offlineServer)).setText(Server.label(loaded == null ? "" : loaded));
        offline.setVisibility(View.VISIBLE);
    }

    /** Only the server's pages in the window. */
    private final class Pages extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri url = request.getUrl();
            if (Server.isOurs(MainActivity.this, url) || "about".equals(url.getScheme())) return false;
            if (!request.isForMainFrame()) return false;
            outside(url);
            return true;
        }

        /** Signing in (or out, or a new password) sets the cookie with no page load after it, and
         *  the WebView saves cookies every 30 seconds: this one goes to disk a moment after, so
         *  the app being closed straight away doesn't sign you out. */
        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            String path = request.getUrl().getPath();
            if ("POST".equals(request.getMethod()) && path != null && path.matches(".*/api/(login|logout|account/password)")
                    && Server.isOurs(MainActivity.this, request.getUrl())) {
                view.postDelayed(() -> CookieManager.getInstance().flush(), 3000);
            }
            return null;
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            if (url == null || !url.equals(failedUrl)) {
                failedUrl = null;
                offline.setVisibility(View.GONE);
                if (forget) {
                    view.clearHistory();
                    forget = false;
                }
            }
            updateBack();
        }

        @Override
        public void doUpdateVisitedHistory(WebView view, String url, boolean reload) {
            updateBack();
        }

        @Override
        public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
            if (request.isForMainFrame()) noAnswer(request.getUrl());
        }

        /** The proxy in front of Olam answered for it: Olam itself is down. */
        @Override
        public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse response) {
            int code = response.getStatusCode();
            if (request.isForMainFrame() && (code == 502 || code == 503 || code == 504)) noAnswer(request.getUrl());
        }

        @Override
        public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
            handler.cancel();
            Uri url = Uri.parse(error.getUrl());
            if (Server.isOurs(MainActivity.this, url)) noAnswer(url);
        }

        /** The page's process went (memory, an update of the WebView): a new window, not a crash. */
        @Override
        public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {
            recreate();
            return true;
        }
    }
}
