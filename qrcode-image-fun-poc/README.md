<img src="app/resources/icon.png" width="128" alt="QR Page Capture" />

# QR Page Capture

Upload an image and get back a printable A4 page whose QR code is painted with that image. Print it into a notebook. Later, point a camera at it once: the app decodes the code on the spot and sends nothing but the 36-character id, so the server proves it signed that id and pairs the page it already holds with the original upload.

This is an implementation of the *Notebook PoC Plan* from [qr-image-qrt-screen-to-camera-poc-09-2026](../../html-research/qr-image-qrt-screen-to-camera-poc-09-2026.html), with the phone replaced by a macOS desktop app.

## How It Works

The optical channel carries **identity, not data**. A 36-character signed id fits a Version 5 EC-H code with room to spare, and HTTPS carries the megabytes.

1. You drop an image. The server mints a 36-character HMAC-signed id.
2. `segno` encodes that id at Version 5, error correction H — 37 modules across.
3. The image is painted behind the code at full strength, and a soft-edged dot is stamped at each module centre to carry that module's value. Function patterns stay solid.
4. The **verification gate** shrinks the rendered page to a 1080p framing, blurs it, tilts it three ways, and decodes. Anything that fails is restyled with a bigger dot and a stronger push of the space between dots toward the module values, up to a plain code.
5. The survivor, rendered at 24 px per module, is downsampled onto an A4 page at 300 DPI with the code at 25 mm.
6. You point the camera at the page. `jsQR` decodes the id in the renderer; no frame ever leaves the machine.
7. The app posts that id alone. The server rejects it unless its own HMAC checks out, then marks the page captured.

QRT, animated QR and fountain codes are all deliberately absent: paper displays exactly one frame forever, and a machine that can upload already has a network.

## Architecture

![architecture](diagrams/architecture.svg)

## Features

- **The capture uploads 36 characters.** The camera frame is decoded in the renderer and thrown away; pairing costs one short JSON body, not a megabyte of PNG.
- **Verification gate before styling.** Nothing ships that a simulated camera cannot decode, which turns a print-and-reprint loop into an in-memory one.
- **Adaptive styling.** Four strength levels, escalating only when the gate refuses, so each page keeps as much picture as it can afford.
- **Signed ids.** The client is the decoder now, so the server trusts nothing it sends: an id pairs only if the server's own HMAC verifies and the id is one it minted.
- **Desktop app with real macOS manners.** Single instance, remembered window position, ⌘K search, ⌘/ shortcuts, ⌘1–4 tabs, zoom, screen capture, full screen.

## Stack

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI + uvicorn | Two endpoints; multipart parsing and validation for free |
| QR generation | segno | Pure Python, zero dependencies, exposes the raw module matrix |
| Scan decoding | jsQR | One MIT file, no dependencies; Electron ships no `BarcodeDetector` |
| Styling and gate | OpenCV + numpy | One library covers compositing and the gate's decoding |
| Desktop app | Electron | The camera, the print dialog and the file save are all one runtime |
| Packaging | electron-packager | Produces a `.app` the install script drops into `/Applications` |

Six Python dependencies, one app dependency and two dev-dependencies. No Pillow (OpenCV does the pixels), no PDF library (a 300 DPI PNG prints). `jsQR` is in the app because Electron's Chromium ships without the Shape Detection API — `BarcodeDetector` is absent even behind its flags, which a probe confirmed before the dependency was added.

### One deviation from the plan

- **`cv2.QRCodeDetector` instead of `pyzbar`.** It removes the `brew install zbar` native dependency. `pyzbar` is the more tolerant decoder, so the gate trades a little decode robustness for one fewer moving part — and being the stricter decoder is what makes it a useful gate.

The client decodes and posts only the id, as the plan has it. The cost is the deskewed capture: rectifying the page needs the frame, and the frame is exactly what is no longer uploaded.

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/uploads` | multipart `image` | `{id, style_attempt, image_strength, code_mm, captured}` |
| `POST` | `/captures` | json `{id}` | the same entry, now `captured: true` |
| `GET` | `/pairs` | — | every entry, sorted by id |
| `GET` | `/pairs/{id}` | — | one entry |
| `GET` | `/pages/{id}.png` | — | the 2480 × 3508 printable page |
| `GET` | `/originals/{id}.png` | — | the uploaded image |

`POST /uploads` answers `422` when no styling survives the gate. `POST /captures` answers `422` for an id whose signature fails or an id this server never minted. Uploads over 12 MB get `413`; anything OpenCV cannot decode gets `415`.

Interactive docs are at `http://127.0.0.1:8000/docs` while the server runs.

## Key Data Structures And Decisions

**The id.** 12 random bytes plus a 10-byte HMAC-SHA256 tag, base32 without padding: 20 + 16 = 36 characters. Base32 is uppercase alphanumeric, so the code uses QR's alphanumeric mode, where Version 5 EC-H holds 64 characters. The payload is comfortably inside the smallest version that still looks like a picture.

**The module matrix.** `segno` exposes the raw 37 × 37 matrix. A separate boolean mask marks the function patterns — finder squares with separators and format information, both timing lines, and the alignment pattern — and those modules are always rendered solid. Only the data and error-correction modules form the styling budget.

**Styling as two layers.** Rather than pasting a logo over part of the code, the picture is the background and the code rides on top as a halftone screen: an antialiased dot of 42% module radius at each module centre. Between the dots the picture is untouched, which is what keeps it recognisable — pushing whole modules toward their true black or white flattens the picture into coloured noise. A `field` factor can push those gaps toward the module value when a picture needs it, and escalation raises the field and the dot radius together; the last step is an unstyled code, the most decodable this geometry gets. Rendering at 24 px per module and downsampling into the 25 mm box antialiases the dots, which the gate measurably prefers over hard-edged ones.

**The gate defines the envelope.** It checks a straight 1080p framing plus three tilt directions with extra blur. That is what the system guarantees. Photographs from angles steeper than that envelope are not promised to pair — and a test pins down that when they fail, they fail cleanly rather than pairing the wrong page.

**Two decoders, deliberately.** The gate decodes with OpenCV in Python; the app decodes with `jsQR` in the renderer. OpenCV is the stricter of the two at this size, so a page that clears the gate is comfortably inside what the app can read.

## How To Run

```bash
./install-deps.sh     # .venv + python deps, then npm install for the app
./run.sh              # FastAPI on http://127.0.0.1:8000
./run-tests.sh        # 10 tests
./app/install.sh      # build and install "QR Page Capture.app" into /Applications
./app/uninstall.sh    # remove it, and its saved window state
```

`install.sh` always uninstalls first, so exactly one version is ever installed. Start the server before the app — the header shows `server up` or `server down`.

```
Ran 10 tests in 1.5s

OK
```

The tests encode the two things that must not break: the gate must reject styling a simulated camera cannot read (and must be *able* to fail, which is asserted directly), and no id reaches the store unless this server minted and signed it. The round trip renders a page, photographs it through a tilt inside the gate's envelope, and asserts the id read back off that photograph is the one that pairs.

## The UI

### 1 · Upload

![upload](printscreens/01-upload.png)

The drop zone takes a file by drag or by click. On success a result card appears with the minted id, which styling attempt survived the gate, and the printed code size — so you can see immediately whether your picture cost the code any margin.

### ⌘K · Search

![search](printscreens/02-search.png)

The search modal lists the four tabs with their shortcuts, then every page id with its state — `captured` or `page only`. Enter on a tab goes there; Enter on an id loads that page into the Page tab.

### 2 · Page

![page](printscreens/03-page.png)

The printable page: A4 at 300 DPI, a ruled notebook body, the id printed in small grey type, and the styled code at 25 mm centred at the bottom. **Print** opens the macOS print dialog; **Save PNG** writes the full-resolution file.

### 3 · Scan

![scan](printscreens/04-scan.png)

Start the camera and hold the code in frame. Every 700 ms the app grabs a frame, decodes it locally, and posts the id if it found one — an in-flight guard keeps a visible code from firing a pile of duplicates, and it stops the moment the server pairs. **Capture now** forces a single attempt and surfaces the server's reason when it refuses.

### 4 · Pairs

![pairs](printscreens/05-pairs.png)

Every page with its two artefacts side by side, the original upload and the printable page, tagged `captured` or `not captured yet`. Since the scan sends only an id, there is no third artefact to show: a capture leaves a state change, not a picture.

### ⌘/ · Shortcuts

![shortcuts](printscreens/06-shortcuts.png)

Every binding the app answers to: ⌘K search, ⌘/ this list, ⌘+ and ⌘- zoom, ⌘1–4 tabs, ⌘P screen capture to the Desktop, ⌘⇧↩ full screen, and the standard cut, copy and paste.

## What This Is Not

No image bytes cross the optical channel — a single QR caps at 2,953 bytes — and none cross the capture POST either. There is no deskewed scan of the page, because straightening it would mean uploading the frame that was deliberately left behind. There is no offline mode, because a machine that can upload has a network. There is no handwriting OCR, and no page identity across a reusable notebook, which is where Rocketbook's real complexity lives and why their timeline is quarters and this one is days.
