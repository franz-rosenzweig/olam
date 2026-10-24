package xyz.tiresia.olam;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;

import java.util.Locale;

/**
 * The Olam server the app shows: its address, kept in the app's own preferences, and which
 * addresses are its pages. Everything else opens outside the app.
 */
final class Server {
    static final String DEMO = "https://stuffs.tiresia.xyz/olam/";

    private Server() { }

    private static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences("server", Context.MODE_PRIVATE);
    }

    /** The address, ending in "/" (the page's paths are relative to it), or null before one is chosen. */
    static String base(Context c) {
        return prefs(c).getString("base", null);
    }

    static void setBase(Context c, String base) {
        prefs(c).edit().putString("base", base).apply();
    }

    /**
     * What was typed, as an address, or null if it isn't one. Without a scheme it's https, except
     * for a server at home, which rarely has a certificate: an IP address, a port, a name with no
     * dot in it, or one ending .local, .lan, .home or .internal is http.
     * "olam.example.com" → https://olam.example.com/, "nas.local:8462" → http://nas.local:8462/
     */
    static String normalize(String typed) {
        String s = typed == null ? "" : typed.trim();
        if (s.isEmpty() || s.matches(".*\\s.*")) return null;
        if (!s.matches("(?i)^https?://.*")) {
            if (s.contains("://")) return null;
            String host = s.replaceFirst("[/?#].*$", "").toLowerCase(Locale.ROOT);
            boolean home = host.contains(":") || host.matches("[0-9.]+") || !host.contains(".")
                    || host.matches(".*\\.(local|lan|home|internal)$");
            s = (home ? "http://" : "https://") + s;
        }
        Uri u = Uri.parse(s);
        if (u.getHost() == null || u.getHost().isEmpty()) return null;
        String path = u.getEncodedPath() == null ? "" : u.getEncodedPath();
        if (!path.endsWith("/")) path += "/";
        return new Uri.Builder().scheme(u.getScheme().toLowerCase(Locale.ROOT))
                .encodedAuthority(u.getEncodedAuthority()).encodedPath(path).build().toString();
    }

    /** https://stuffs.tiresia.xyz/olam/ → stuffs.tiresia.xyz/olam */
    static String label(String base) {
        return base.replaceFirst("^https?://", "").replaceFirst("/$", "");
    }

    /**
     * One of the server's pages: its host and port, under its path. http and https count as the
     * same, so a server that sends http on to https stays in the app.
     */
    static boolean isOurs(Context c, Uri url) {
        String base = base(c);
        if (base == null || url == null || url.getHost() == null) return false;
        Uri b = Uri.parse(base);
        String scheme = url.getScheme() == null ? "" : url.getScheme().toLowerCase(Locale.ROOT);
        if (!scheme.equals("http") && !scheme.equals("https")) return false;
        if (!url.getHost().equalsIgnoreCase(b.getHost())) return false;
        if (port(url) != port(b) && !(url.getPort() == -1 && b.getPort() == -1)) return false;
        String path = url.getEncodedPath() == null || url.getEncodedPath().isEmpty() ? "/" : url.getEncodedPath();
        return path.startsWith(b.getEncodedPath()) || (path + "/").equals(b.getEncodedPath());
    }

    private static int port(Uri u) {
        if (u.getPort() != -1) return u.getPort();
        return "https".equalsIgnoreCase(u.getScheme()) ? 443 : 80;
    }
}
