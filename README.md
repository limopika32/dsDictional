# dsDictional
金沢工業大学 電子計算機研究会用に開発した簡易図書システム

:warning: pip による `sendgrid pygame nfcpy requests` のライブラリインストールが必要です。
また実行環境には、メール送信のためにインターネット接続が必要になります。
```
python -m pip install sendgrid pygame nfcpy requests
pip install sendgrid pygame nfcpy requests
```

## ファイル
+ `dict/master.csv` に書籍 `{ISBN, 書籍名}` を予め登録してください。
+ `dict/public.csv` には貸し出された書籍情報が記録されます。
+ `usr/master.csv` に利用者名簿 `{学籍番号, 名前}` を予め登録してください。
+ `usr/XXXX.csv` (`XXXX`は学籍番号) には利用者の貸出状況と設定情報が記録されます。
+ `log/XXXX.log` (`XXXX`は年月日8桁) には貸出返却の詳細情報が随時記録されます。

## 使用方法
1. `start.bat` を起動するか `main.py` を実行します。
2. 利用者がシステムを利用できる状態になります。(詳細は [userManual.pdf](./userManual.pdf) を確認してください)。
+ 毎日 0:00 に貸出延滞者に対してメールが送信されます。
3. 間違えてウィンドウを閉じて終了しても、再度 1. からやり直すことでシステムを再開することが出来ます。


***
> nakanolab による [NFC対応学生証による出席確認ツール](https://github.com/nakanolab/nfc-attendance) のソースを利用しています。