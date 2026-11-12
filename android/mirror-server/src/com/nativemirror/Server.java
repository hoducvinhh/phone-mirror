package com.nativemirror;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

import android.net.LocalServerSocket;
import android.net.LocalSocket;
import android.media.MediaCodec;
import android.media.MediaCodecInfo;
import android.media.MediaFormat;
import android.os.IBinder;
import android.os.SystemClock;
import android.view.Surface;
import android.view.InputDevice;
import android.view.InputEvent;
import android.view.KeyEvent;
import android.view.MotionEvent;

public final class Server {
    private static volatile LocalSocket client;

    public static void main(String[] args) throws Exception {
        int port = 27183;
        for (int i = 0; i + 1 < args.length; i++) {
            if ("--port".equals(args[i])) port = Integer.parseInt(args[i + 1]);
        }
        LocalServerSocket local = new LocalServerSocket("nativemirror");
        while (true) {
            LocalSocket socket = local.accept();
            client = socket;
            new Thread(() -> handle(socket)).start();
        }
    }

    private static void handle(LocalSocket socket) {
        try {
            DataInputStream input = new DataInputStream(socket.getInputStream());
            DataOutputStream output = new DataOutputStream(socket.getOutputStream());
            Capture capture = new Capture(output);
            Thread captureThread = new Thread(capture);
            captureThread.start();
            while (client != null) {
                byte[] header = new byte[8];
                input.readFully(header);
                if (!"NMR2".equals(new String(header, 0, 4, StandardCharsets.US_ASCII))) continue;
                int length = ByteBuffer.wrap(header, 4, 4).getInt();
                byte[] packet = new byte[length];
                input.readFully(packet);
                handleInput(packet);
            }
        } catch (IOException ignored) {
            client = null;
        }
    }

    private static void handleInput(byte[] packet) {
        if (packet.length < 1) return;
        int action = packet[0] & 0xff;

        if (action == 6) {
            if (packet.length == 1) return;
            String text = new String(packet, 1, packet.length - 1, StandardCharsets.UTF_8);
            injectText(text);
            return;
        }
        if (action >= 7) {
            injectKey(action);
            return;
        }
        if (packet.length < 9) return;
        int id = ByteBuffer.wrap(packet, 1, 4).getInt();
        int x = ByteBuffer.wrap(packet, 5, 2).getShort() & 0xffff;
        int y = ByteBuffer.wrap(packet, 7, 2).getShort() & 0xffff;

        MotionEvent event = createTouchEvent(action, id, x, y);
        if (event != null) {
            injectEvent(event);
            event.recycle();
        }
    }

    private static MotionEvent createTouchEvent(int action, int id, int x, int y) {
        int androidAction;
        if (action == 1) androidAction = MotionEvent.ACTION_DOWN;
        else if (action == 3) androidAction = MotionEvent.ACTION_UP;
        else androidAction = MotionEvent.ACTION_MOVE;

        MotionEvent.PointerProperties[] properties = new MotionEvent.PointerProperties[1];
        properties[0] = new MotionEvent.PointerProperties();
        properties[0].id = id;
        properties[0].toolType = MotionEvent.TOOL_TYPE_FINGER;

        MotionEvent.PointerCoords[] coords = new MotionEvent.PointerCoords[1];
        coords[0] = new MotionEvent.PointerCoords();
        coords[0].x = x;
        coords[0].y = y;
        coords[0].pressure = (action == 3) ? 0.0f : 1.0f;
        coords[0].size = 1.0f;

        long now = SystemClock.uptimeMillis();
        return MotionEvent.obtain(
                now,
                now,
                androidAction,
                1,
                properties,
                coords,
                0,                          // metaState
                0,                          // buttonState
                1.0f,                       // xPrecision
                1.0f,                       // yPrecision
                0,                          // deviceId
                0,                          // edgeFlags
                InputDevice.SOURCE_TOUCHSCREEN, // source
                0                           // flags
        );
    }

    private static void injectEvent(InputEvent event) {
        try {
            Class<?> inputManagerClass = Class.forName("android.hardware.input.InputManager");
            Method getInstance = inputManagerClass.getMethod("getInstance");
            Object inputManager = getInstance.invoke(null);
            Method inject = inputManagerClass.getMethod("injectInputEvent",
                    InputEvent.class, int.class);
            inject.invoke(inputManager, event, 2);
        } catch (Throwable ignored) {
        }
    }

    private static void injectText(String text) {
        for (int i = 0; i < text.length(); i++) {
            char character = text.charAt(i);
            if (character >= 'a' && character <= 'z') {
                injectKeyEvent(character - 'a' + KeyEvent.KEYCODE_A, 0);
            } else if (character >= 'A' && character <= 'Z') {
                injectKeyEvent(character - 'A' + KeyEvent.KEYCODE_A, KeyEvent.META_SHIFT_ON);
            } else if (character >= '0' && character <= '9') {
                injectKeyEvent(character - '0' + KeyEvent.KEYCODE_0, 0);
            } else if (character == ' ') {
                injectKeyEvent(KeyEvent.KEYCODE_SPACE, 0);
            } else if (character == '\n') {
                injectKeyEvent(KeyEvent.KEYCODE_ENTER, 0);
            } else if (character == '.') {
                injectKeyEvent(KeyEvent.KEYCODE_PERIOD, 0);
            } else if (character == ',') {
                injectKeyEvent(KeyEvent.KEYCODE_COMMA, 0);
            } else if (character == '/') {
                injectKeyEvent(KeyEvent.KEYCODE_SLASH, 0);
            } else if (character == '-') {
                injectKeyEvent(KeyEvent.KEYCODE_MINUS, 0);
            }
        }
    }

    private static void injectKey(int action) {
        int keyCode;
        switch (action) {
            case 7: keyCode = KeyEvent.KEYCODE_BACK; break;
            case 8: keyCode = KeyEvent.KEYCODE_HOME; break;
            case 9: keyCode = KeyEvent.KEYCODE_APP_SWITCH; break;
            case 10: keyCode = KeyEvent.KEYCODE_POWER; break;
            case 11: keyCode = KeyEvent.KEYCODE_VOLUME_UP; break;
            case 12: keyCode = KeyEvent.KEYCODE_VOLUME_DOWN; break;
            default: return;
        }
        injectKeyEvent(keyCode, 0);
    }

    private static void injectKeyEvent(int keyCode, int meta) {
        long now = SystemClock.uptimeMillis();
        injectEvent(new KeyEvent(now, now, KeyEvent.ACTION_DOWN, keyCode, 0, meta,
                0, 0, 0, InputDevice.SOURCE_KEYBOARD));
        injectEvent(new KeyEvent(now, now, KeyEvent.ACTION_UP, keyCode, 0, meta,
                0, 0, 0, InputDevice.SOURCE_KEYBOARD));
    }

    private static final class Capture implements Runnable {
        private final DataOutputStream output;

        Capture(DataOutputStream output) {
            this.output = output;
        }

        public void run() {
            MediaCodec codec = null;
            try {
                codec = MediaCodec.createEncoderByType("video/avc");
                MediaFormat format = MediaFormat.createVideoFormat("video/avc", 1080, 1920);
                format.setInteger(MediaFormat.KEY_BIT_RATE, 8_000_000);
                format.setInteger(MediaFormat.KEY_FRAME_RATE, 60);
                format.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 1);
                format.setInteger(MediaFormat.KEY_COLOR_FORMAT,
                        MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface);
                format.setInteger(MediaFormat.KEY_PROFILE,
                        MediaCodecInfo.CodecProfileLevel.AVCProfileHigh);
                format.setInteger(MediaFormat.KEY_LEVEL,
                        MediaCodecInfo.CodecProfileLevel.AVCLevel32);
                try {
                    format.setInteger(MediaFormat.KEY_LATENCY, 0);
                    format.setInteger(MediaFormat.KEY_PRIORITY, 0);
                } catch (Throwable ignored) {}

                codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE);
                IBinder display = createVirtualDisplay();
                Surface inputSurface = codec.createInputSurface();
                bindSurface(display, inputSurface);
                codec.start();
                encodeLoop(codec);
                unbindSurface(display);
            } catch (Throwable error) {
                error.printStackTrace();
            } finally {
                if (codec != null) codec.release();
            }
        }

        private IBinder createVirtualDisplay() throws Exception {
            Class<?> surfaceControl = Class.forName("android.view.SurfaceControl");
            Method createDisplay = surfaceControl.getMethod("createDisplay",
                    String.class, boolean.class);
            return (IBinder) createDisplay.invoke(null, "Appcuatao", false);
        }

        private void bindSurface(IBinder display, Surface surface) throws Exception {
            Class<?> surfaceControl = Class.forName("android.view.SurfaceControl");
            Method setDisplaySurface = surfaceControl.getMethod(
                    "setDisplaySurface", IBinder.class, Surface.class);
            setDisplaySurface.invoke(null, display, surface);

            Method setDisplayProjection = surfaceControl.getMethod(
                    "setDisplayProjection", IBinder.class, int.class,
                    android.graphics.Rect.class, android.graphics.Rect.class);
            setDisplayProjection.invoke(null, display, 0,
                    new android.graphics.Rect(0, 0, 1080, 1920),
                    new android.graphics.Rect(0, 0, 1080, 1920));

            Method setDisplayLayerStack = surfaceControl.getMethod(
                    "setDisplayLayerStack", IBinder.class, int.class);
            setDisplayLayerStack.invoke(null, display, 0);
        }

        private void unbindSurface(IBinder display) throws Exception {
            Class<?> surfaceControl = Class.forName("android.view.SurfaceControl");
            Method setDisplaySurface = surfaceControl.getMethod(
                    "setDisplaySurface", IBinder.class, Surface.class);
            setDisplaySurface.invoke(null, display, null);
        }

        private void encodeLoop(MediaCodec codec) throws IOException {
            MediaCodec.BufferInfo info = new MediaCodec.BufferInfo();
            while (client != null) {
                int index = codec.dequeueOutputBuffer(info, 1000);
                if (index >= 0) {
                    java.nio.ByteBuffer buffer = codec.getOutputBuffer(index);
                    byte[] frame = new byte[info.size];
                    buffer.position(info.offset);
                    buffer.get(frame);
                    synchronized (output) {
                        output.writeBytes("NMR2");
                        output.writeInt(frame.length);
                        output.write(frame);
                        output.flush();
                    }
                    codec.releaseOutputBuffer(index, false);
                } else if (index == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
                    MediaFormat format = codec.getOutputFormat();
                }
            }
        }
    }
}
