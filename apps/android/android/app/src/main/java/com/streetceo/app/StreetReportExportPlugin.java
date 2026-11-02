package com.streetceo.app;

import android.content.ClipData;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.pdf.PdfDocument;
import android.net.Uri;
import androidx.core.content.FileProvider;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

/** User-initiated report files only; no arbitrary paths, HTML, URLs or storage permissions. */
@CapacitorPlugin(name = "StreetReportExport")
public class StreetReportExportPlugin extends Plugin {
    private File target(PluginCall call, String extension) throws Exception {
        String name = call.getString("filename", "");
        if (!name.matches("street-ceo-(sales|profit)-[0-9]{4}-[0-9]{2}-[0-9]{2}-to-[0-9]{4}-[0-9]{2}-[0-9]{2}")) throw new IllegalArgumentException();
        File directory = new File(getContext().getCacheDir(), "report-exports").getCanonicalFile();
        if (!directory.exists() && !directory.mkdirs()) throw new IllegalStateException();
        File file = new File(directory, name + "-" + UUID.randomUUID() + "." + extension).getCanonicalFile();
        if (!directory.equals(file.getParentFile())) throw new IllegalArgumentException();
        return file;
    }
    private void share(PluginCall call, File file, String mime) {
        getActivity().runOnUiThread(() -> {
            try {
                Uri uri = FileProvider.getUriForFile(getContext(), getContext().getPackageName() + ".reports", file);
                Intent intent = new Intent(Intent.ACTION_SEND).setType(mime);
                intent.putExtra(Intent.EXTRA_STREAM, uri);
                intent.putExtra(Intent.EXTRA_SUBJECT, "Street CEO report");
                intent.setClipData(ClipData.newRawUri("Street CEO report", uri));
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                getActivity().startActivity(Intent.createChooser(intent, "Share Street CEO report"));
                JSObject result = new JSObject(); result.put("shareSheetOpened", true); call.resolve(result);
            } catch (Exception failure) { call.reject("Could not open report sharing. Choose an app that can receive this file."); }
        });
    }
    @PluginMethod public void shareCsv(PluginCall call) {
        try {
            String content = call.getString("content", ""); byte[] bytes = content.getBytes(StandardCharsets.UTF_8);
            if (bytes.length == 0 || bytes.length > 2_000_000) throw new IllegalArgumentException();
            File file = target(call, "csv");
            try (FileOutputStream output = new FileOutputStream(file)) { output.write(bytes); }
            share(call, file, "text/csv");
        } catch (Exception failure) { call.reject("Could not prepare CSV. Select a smaller report and try again."); }
    }
    @PluginMethod public void sharePdf(PluginCall call) {
        File file = null;
        try {
            String title = call.getString("title", ""); String subtitle = call.getString("subtitle", ""); JSArray rows = call.getArray("rows");
            if (!(title.equals("Sales report") || title.equals("Product gross profit report")) || subtitle.length() > 300 || rows == null || rows.length() > 3000) throw new IllegalArgumentException();
            int characters = 0;
            for (int index = 0; index < rows.length(); index++) {
                JSONObject row = rows.getJSONObject(index); String kind = row.getString("kind"), text = row.getString("text");
                if (!(kind.equals("heading") || kind.equals("text")) || text.length() > 2000) throw new IllegalArgumentException();
                characters += text.length();
            }
            if (characters > 500_000) throw new IllegalArgumentException();
            file = target(call, "pdf");
            PdfDocument document = new PdfDocument();
            try {
                Painter painter = new Painter(document, title, subtitle);
                for (int index = 0; index < rows.length(); index++) {
                    JSONObject row = rows.getJSONObject(index); painter.row(row.getString("kind"), row.getString("text"));
                }
                painter.finish();
                try (FileOutputStream output = new FileOutputStream(file)) { document.writeTo(output); }
            } finally { document.close(); }
            share(call, file, "application/pdf");
        } catch (Exception failure) { if (file != null) file.delete(); call.reject("Could not prepare PDF. Select a smaller report and try again."); }
    }
    private class Painter {
        final PdfDocument document; final String title, subtitle; final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        final Bitmap logo = BitmapFactory.decodeResource(getContext().getResources(), R.drawable.street_ceo_logo);
        PdfDocument.Page page; Canvas canvas; int number = 0; float y;
        Painter(PdfDocument document, String title, String subtitle) { this.document = document; this.title = title; this.subtitle = subtitle; start(); }
        void start() {
            if (++number > 100) throw new IllegalArgumentException();
            page = document.startPage(new PdfDocument.PageInfo.Builder(595, 842, number).create()); canvas = page.getCanvas();
            canvas.drawColor(Color.WHITE);
            if (logo != null) canvas.drawBitmap(logo, null, new RectF(36, 26, 92, 82), paint);
            paint.setColor(Color.rgb(25, 77, 57)); paint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD)); paint.setTextSize(22); canvas.drawText("Street CEO", 108, 43, paint);
            paint.setTextSize(13); canvas.drawText(title, 108, 64, paint);
            paint.setTypeface(Typeface.DEFAULT); paint.setTextSize(9); paint.setColor(Color.rgb(105, 127, 94));
            // Subtitle is bounded; wrap instead of clipping long timezone names.
            float top = 82; String remaining = plain(subtitle);
            while (!remaining.isEmpty()) { int end = Math.max(1, paint.breakText(remaining, true, 449, null)); canvas.drawText(remaining.substring(0, end), 108, top, paint); remaining = remaining.substring(end); top += 12; }
            paint.setColor(Color.rgb(38, 112, 78)); canvas.drawRect(36, Math.max(100, top), 559, Math.max(100, top) + 2, paint); y = Math.max(122, top + 24);
            paint.setTextSize(9); paint.setColor(Color.rgb(115, 137, 100)); canvas.drawText("Street CEO | Saved records | Page " + number, 36, 815, paint);
        }
        String plain(String value) { return value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').replaceAll("[\\p{Cntrl}]", " "); }
        void row(String kind, String value) {
            boolean heading = kind.equals("heading"); y += heading ? 11 : 3;
            paint.setTypeface(Typeface.create(Typeface.DEFAULT, heading ? Typeface.BOLD : Typeface.NORMAL)); paint.setTextSize(heading ? 13 : 10.5f); paint.setColor(heading ? Color.rgb(26, 87, 59) : Color.rgb(68, 91, 59));
            String remaining = plain(value);
            while (!remaining.isEmpty()) {
                if (y + 17 > 780) { document.finishPage(page); start(); paint.setTypeface(Typeface.create(Typeface.DEFAULT, heading ? Typeface.BOLD : Typeface.NORMAL)); paint.setTextSize(heading ? 13 : 10.5f); paint.setColor(heading ? Color.rgb(26, 87, 59) : Color.rgb(68, 91, 59)); }
                int end = Math.max(1, paint.breakText(remaining, true, 523, null));
                if (end < remaining.length()) { int space = remaining.lastIndexOf(' ', end); if (space > end / 2) end = space; }
                canvas.drawText(remaining.substring(0, end), 36, y, paint); remaining = remaining.substring(end).trim(); y += heading ? 18 : 15;
            }
        }
        void finish() { document.finishPage(page); if (logo != null) logo.recycle(); }
    }
}
