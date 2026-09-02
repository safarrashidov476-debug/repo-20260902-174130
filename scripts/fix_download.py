#!/usr/bin/env python3
"""
Tiflogram: yuklash tugashi tovushi + Tiflogram papkasiga saqlash.
Rejimlar: check / apply
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    # --- Papka nomlari: Telegram -> Tiflogram OLIB TASHLANDI ---
    # Sabab: bu 9 ta almashtirish ImageLoader.java faylidagi BARCHA
    # "Telegram" nomlanishini qamrab olmaydi (masalan MediaStore/
    # scoped-storage yo'llarida boshqacha yozilgan bo'lishi mumkin).
    # Natijada bir joyda "Tiflogram", boshqa joyda hali "Telegram"
    # kutiladi -> nomlar mos kelmay, ilova ishga tushishida cheksiz
    # kutib, ~30 soniyadan keyin tizim tomonidan to'xtatiladi (ANR).
    # Xavfsizlik uchun papka nomi asl "Telegram" holida qoldiriladi;
    # faqat ilova nomi/brendi "Tiflogram" bo'lib qoladi (fix_branding.py).
    # --- Yuklash tugashi: tovush + TalkBack ---
    {
        "id": 10,
        "label": "DownloadController: fileLoaded -> tovush va ogohlantirish",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/DownloadController.java",
        "old": '''        } else if (id == NotificationCenter.fileLoaded || id == NotificationCenter.httpFileDidLoad) {
            listenerInProgress = true;
            String fileName = (String) args[0];''',
        "new": '''        } else if (id == NotificationCenter.fileLoaded || id == NotificationCenter.httpFileDidLoad) {
            listenerInProgress = true;
            String fileName = (String) args[0];
            // Tiflogram: tovush FAQAT foydalanuvchi o'zi boshlagan
            // yuklamada chalinsin (avtomatik/fon yuklamalarida emas).
            // downloadingFiles - hozir ketayotgan; recentDownloadingFiles -
            // yaqinda tugagan (ba'zan element aynan shu bildirishnoma
            // paytida bittasidan ikkinchisiga ko'chirilgan bo'lishi
            // mumkin, shuning uchun ikkalasini ham tekshiramiz).
            boolean tiflogramIsUserDownload = false;
            for (int _i = 0; _i < downloadingFiles.size() && !tiflogramIsUserDownload; _i++) {
                MessageObject _mo = downloadingFiles.get(_i);
                if (_mo != null && _mo.getDocument() != null &&
                        fileName.equals(FileLoader.getAttachFileName(_mo.getDocument()))) {
                    tiflogramIsUserDownload = true;
                }
            }
            if (!tiflogramIsUserDownload) {
                for (int _i = 0; _i < recentDownloadingFiles.size() && !tiflogramIsUserDownload; _i++) {
                    MessageObject _mo = recentDownloadingFiles.get(_i);
                    if (_mo != null && _mo.getDocument() != null &&
                            fileName.equals(FileLoader.getAttachFileName(_mo.getDocument()))) {
                        tiflogramIsUserDownload = true;
                    }
                }
            }
            FileLog.d("TiflogramSound fileName=" + fileName + " match=" + tiflogramIsUserDownload
                    + " downloadingFiles.size=" + downloadingFiles.size()
                    + " recentDownloadingFiles.size=" + recentDownloadingFiles.size());
            if (tiflogramIsUserDownload) {
                try {
                    android.media.MediaPlayer mp = android.media.MediaPlayer.create(
                            ApplicationLoader.applicationContext,
                            org.telegram.messenger.R.raw.tiflogram_dl_done);
                    if (mp != null) {
                        mp.setOnCompletionListener(android.media.MediaPlayer::release);
                        mp.start();
                    }
                } catch (Throwable ignore) {
                }
            }''',
    },
]


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def main():
    if MODE not in ("check", "apply"):
        print(f"Noma'lum rejim: {MODE}")
        sys.exit(1)

    print(f"=== Rejim: {MODE} (yuklash papkasi + tovush) ===\n")
    results = []
    file_cache = {}

    for fix in FIXES:
        path = fix["path"]
        if path not in file_cache:
            file_cache[path] = read_file(path)
        content = file_cache[path]
        if content is None:
            print(f"❌ [{fix['id']}] {fix['label']} — fayl topilmadi")
            results.append(False)
            continue
        if fix["old"] not in content:
            print(f"❌ [{fix['id']}] {fix['label']} — eski matn topilmadi")
            results.append(False)
            continue
        print(f"✅ [{fix['id']}] {fix['label']}")
        results.append(True)

    failed = results.count(False)
    print(f"\nOK: {len(results)-failed}/{len(results)}")
    if MODE == "check":
        sys.exit(1 if failed else 0)
    if failed:
        print("⛔ Hech narsa o'zgartirilmadi")
        sys.exit(1)

    modified = dict(file_cache)
    for fix in FIXES:
        path = fix["path"]
        if fix.get("replace_all"):
            modified[path] = modified[path].replace(fix["old"], fix["new"])
        else:
            modified[path] = modified[path].replace(fix["old"], fix["new"], 1)

    for path, content in modified.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Yozildi: {path}")
    print("\n✅ Yuklash papkasi va tovush patchlari qo'llandi.")


if __name__ == "__main__":
    main()
