# LARAS — Ringkasan Proyek

**LARAS (Logistik Adaptif, Responsif, dan Automasi Sistem)** adalah rancangan aplikasi web B2B berbasis agen kecerdasan buatan untuk membantu operasional persediaan, pengadaan, pelaporan, pengiriman, dan katalog toko daring.

Pemilik usaha merupakan pelanggan utama. Pemilik dan karyawan dapat menggunakan aplikasi melalui percakapan serta tampilan kerja yang terstruktur. Sistem memahami permintaan, mengambil data yang relevan, mengoordinasikan pekerjaan, dan meminta persetujuan sebelum tindakan yang memerlukan otorisasi dijalankan.

Proyek kelompok 13 ini mengangkat ketidakefisienan logistik dan rantai pasok serta berkaitan dengan SDG 9: industri, inovasi, dan infrastruktur.

**Diperbarui: 23 Oktober 2026.** Dokumen ini merangkum konteks dan arah perencanaan. Fitur yang disebutkan tidak otomatis berarti sudah tersedia dalam implementasi. Kinerja, kapasitas, biaya aktual, dan hasil penghematan belum terukur.

## Masalah yang ditangani

- Pencatatan, pelaporan, dan koordinasi manual yang menyita waktu serta berpotensi menimbulkan kesalahan.
- Kompetensi digital pengguna yang beragam dan kebutuhan antarmuka yang mudah dipahami.
- Pergantian karyawan yang dapat mengganggu kesinambungan informasi dan menambah waktu adaptasi.
- Entri katalog produk berulang dengan kategori dan atribut berbeda di setiap marketplace.
- Pengadaan terlambat, pembelian berlebih, serta kesulitan melacak pesanan ke pemasok dan penerimaan barang.

## Pelanggan dan pengguna

LARAS ditujukan kepada pelaku usaha kecil dan menengah yang menangani persediaan, administrasi logistik, pengadaan, penjadwalan pengiriman, dan toko daring.

- **Pelanggan:** pemilik usaha yang membeli layanan LARAS.
- **Pengguna:** pemilik dan karyawan sesuai tanggung jawab serta hak akses masing-masing.
- **Arah produk:** layanan B2B untuk banyak perusahaan, dengan rencana melayani beberapa wilayah. Produk akhir membutuhkan kapasitas dan keandalan layanan produksi; pengembangan lokal hanya merupakan tahap pengembangan.

## Pemilik bekerja sendiri atau bersama karyawan

LARAS mendukung dua susunan kerja yang dapat dipadukan:

1. **Pemilik bekerja sendiri:** AI membantu pekerjaan administratif dan menyiapkan keputusan; pemilik menangani pemeriksaan fisik, pengecualian, dan persetujuan.
2. **Pemilik bersama karyawan:** AI membantu karyawan menyelesaikan tanggung jawab, sementara pemilik mendelegasikan pekerjaan, melihat perkembangan, dan mengatur kewenangan.

Penanggung jawab ditentukan per aktivitas. Pemilik dapat menangani katalog sendiri sambil menyerahkan pemeriksaan stok dan persiapan pengiriman kepada karyawan. Pelaksana tugas dan pemberi persetujuan dapat berbeda.

Usulan fondasi kolaborasi meliputi akun pribadi, tugas dengan penanggung jawab dan status, antrean persetujuan, serta riwayat aktivitas bersama. Percakapan dapat menghasilkan tugas yang tetap dapat dilacak setelah sesi percakapan berakhir. Hak akses harus ditegakkan oleh backend.

AI membantu mengoordinasikan pekerjaan fisik; penghitungan, pengepakan, penyerahan, dan penerimaan barang tetap memerlukan manusia atau sistem fisik yang terintegrasi.

## Enam agen LARAS

| Agen | Peran | Contoh tugas |
| --- | --- | --- |
| **Operator AI** | Pusat percakapan: memahami tujuan, meminta informasi yang kurang, mengatur pekerjaan, dan menggabungkan hasil agen. | “Cek stok menipis dan siapkan usulan pembelian untuk saya tinjau.” |
| **Inventory Agent** | Memeriksa persediaan, mengidentifikasi kekurangan atau selisih stok, dan menggunakan fungsi backend untuk perubahan stok yang tervalidasi. | Menampilkan produk di bawah batas minimum. |
| **Procurement Agent** | Menyiapkan rencana pengadaan, membandingkan informasi pemasok, menyusun usulan pembelian, dan melacak pesanan sampai penerimaan. | Mengusulkan pembelian ulang sesuai kebutuhan dan anggaran. |
| **Reporting Agent** | Mengambil data melalui backend dan menyusun laporan beserta penjelasannya. | Menyiapkan laporan stok, pengadaan, dan pengiriman mingguan. |
| **Dispatch Agent** | Menyiapkan usulan jadwal pengiriman berdasarkan pesanan, stok, kapasitas, dan aturan operasional. | Menyusun jadwal pengiriman untuk persetujuan pengguna. |
| **Store Manager** | Menyiapkan katalog internal untuk publikasi atau pembaruan produk melalui konektor marketplace. | Menyiapkan pratinjau produk untuk Tokopedia dan, pada tahap berikutnya, Shopee. |

**Jumlah agen: satu Operator AI dan lima agen khusus.** Procurement Agent ditambahkan ke rancangan. Orchestrator merupakan fungsi koordinasi di dalam Operator AI, bukan agen ketujuh. Communication/Messaging Agent dan Order Management Agent belum termasuk cakupan yang disepakati.

Tidak setiap pekerjaan memanggil seluruh agen. Agen dapat berjalan dalam layanan backend yang sama dan menggunakan model yang sama dengan instruksi serta alat berbeda.

## Procurement Agent

Pengadaan mencakup penentuan barang yang perlu dibeli, jumlah, pemasok, waktu pemesanan, serta pelacakan hingga barang diterima dan diperiksa.

Tujuannya adalah mengurangi risiko kehabisan stok, pembelian berlebih, biaya pembelian yang tidak terkendali, serta pesanan pemasok yang tidak terlacak.

### Alur yang direncanakan

1. Inventory Agent menyediakan kondisi stok dan kebutuhan pengisian ulang berdasarkan data yang tersedia.
2. Procurement Agent memeriksa permintaan, stok yang sudah ada, pesanan pembelian yang masih terbuka, waktu pasok, jumlah minimum pembelian, dan batas anggaran.
3. Agen membandingkan informasi pemasok yang tercatat atau penawaran yang diberikan pengguna.
4. Sistem menghitung dan memvalidasi jumlah serta biaya melalui backend.
5. Agen menyiapkan usulan pembelian: barang, jumlah, pemasok, perkiraan biaya, estimasi kedatangan, dan alasan rekomendasi.
6. Pemilik atau pengguna berwenang memeriksa dan menyetujui usulan tersebut.
7. Setelah pesanan benar-benar ditempatkan melalui pengguna atau integrasi yang tersedia, sistem mencatatnya dan melacak statusnya.
8. Pengguna mengonfirmasi barang yang diterima, termasuk kekurangan, kerusakan, atau perbedaan jumlah.
9. Backend mencatat penerimaan dan memperbarui stok melalui alur Inventory yang tervalidasi. Reporting Agent dapat menggunakan catatan ini untuk laporan.

**Batas tanggung jawab:** Inventory menjaga catatan persediaan; Procurement mengelola kebutuhan dan proses pembelian. Pesanan pembelian yang disetujui atau dikirim ke pemasok belum berarti barang sudah masuk stok.

Untuk tahap awal, Procurement menggunakan data pemasok yang tersimpan atau dimasukkan pengguna dan menghasilkan usulan pembelian. Menghubungi pemasok, menempatkan pesanan, dan melakukan pembayaran memerlukan integrasi serta kewenangan tersendiri. Pembayaran otomatis belum menjadi cakupan awal.

Pemilik yang bekerja sendiri meninjau usulan dan menerima barang. Dalam tim, karyawan dapat mengumpulkan penawaran atau memeriksa penerimaan, dengan persetujuan belanja mengikuti kewenangan yang diberikan.

## Alur kerja umum

1. Pengguna mengirimkan permintaan melalui percakapan atau tampilan kerja.
2. Operator AI memahami tujuan, memeriksa konteks pengguna, dan meminta informasi penting yang belum lengkap.
3. Sistem menentukan agen, alat, penanggung jawab manusia, dan urutan pekerjaan yang diperlukan.
4. Agen mengambil informasi sesuai perusahaan dan hak akses pengguna.
5. Backend menjalankan kueri, perhitungan, validasi, dan aturan operasional.
6. Pengguna berwenang meninjau tindakan yang memerlukan persetujuan.
7. Backend menjalankan tindakan yang disetujui dan menyimpan hasil serta riwayatnya.
8. Operator AI menyampaikan status yang sesuai dengan hasil sebenarnya, termasuk kegagalan atau pekerjaan yang masih menunggu.

## Data, memori, dan konteks model

Riwayat interaksi, ringkasan pekerjaan, tugas, dan data bisnis disimpan oleh LARAS. Penyimpanan ini terpisah dari layanan model.

Pada setiap panggilan model, backend menyusun input yang dapat mencakup instruksi agen, pesan pengguna, konteks percakapan yang relevan, data hasil retrieval, definisi alat, hasil alat, dan aturan format keluaran. File proyek seperti `AGENTS.md` tidak otomatis dibaca model; isinya hanya menjadi input jika aplikasi memasukkannya.

Untuk percakapan yang berlanjut, LARAS merencanakan penggunaan pesan terbaru, ringkasan interaksi lama, dan retrieval sesuai kebutuhan. Riwayat lengkap tidak perlu dikirim tanpa batas pada setiap permintaan. Percakapan baru dipisahkan dari percakapan sebelumnya kecuali konteks yang relevan sengaja diambil dengan hak akses yang sesuai.

**RAG direncanakan bagi semua agen yang membutuhkan konteks**, termasuk Procurement. Sumbernya dapat berupa prosedur, dokumen, katalog, informasi pemasok, dan riwayat aktivitas. Data operasional yang harus terkini, seperti stok, pesanan pembelian terbuka, dan status publikasi, diambil langsung dari basis data atau API.

Satu permintaan pengguna dapat menghasilkan beberapa panggilan model. Perhitungan biaya dan waktu harus menjumlahkan seluruh panggilan tersebut, termasuk input yang berulang dan keluaran penalaran jika digunakan. Cache bergantung pada model dan penyedia; tidak dapat diasumsikan tersedia untuk setiap deployment.

## Store Manager dan integrasi marketplace

Tujuan Store Manager tetap menyiapkan produk dari satu katalog untuk beberapa marketplace. **Prioritas eksplorasi integrasi saat ini adalah Tokopedia; Shopee menyusul.**

Alur yang direncanakan:

1. LARAS mendaftarkan aplikasi pengembang dan memperoleh kredensial aplikasi platform.
2. Setiap pemilik toko mengotorisasi akses tokonya melalui alur platform.
3. Backend menyimpan token per perusahaan/toko dan menangani pembaruan serta pencabutan akses.
4. Agen menyiapkan nama, deskripsi, gambar, kategori, atribut, harga, variasi, berat, dan data stok dari sumber yang sesuai.
5. Backend memvalidasi data; pengguna melihat pratinjau dan menyetujui publikasi.
6. Konektor menjalankan permintaan, mencatat ID produk, status, dan kesalahan, serta mencegah publikasi ganda saat percobaan ulang.

Kredensial aplikasi dan token toko disimpan di backend, bukan diberikan kepada model atau disertakan dalam prompt. Otorisasi platform dan persetujuan tindakan di LARAS merupakan dua hal terpisah: toko yang terhubung tidak otomatis mengizinkan setiap tindakan tanpa kontrol internal.

### Tokopedia

Penelusuran dalam percakapan mengarah ke TikTok Shop Partner Center sebagai jalur integrasi setelah migrasi API Tokopedia. Dokumentasi yang dibahas mencakup dukungan listing Tokopedia untuk penjual yang telah bermigrasi. Kelayakan toko, operasi produk yang didukung, cakupan izin, kategori aplikasi, dan persyaratan peluncuran perlu dikonfirmasi melalui Partner Center.

Karena LARAS ditujukan untuk banyak bisnis, jalur public app merupakan kandidat awal. Pilihan developer/app dan persyaratan review belum dipastikan untuk akun LARAS.

**Status penyiapan akun:** proses browser dihentikan atas permintaan pengguna setelah halaman pendaftaran dibuka. Tidak ada akun atau aplikasi yang dibuat dan tidak ada kredensial yang diserahkan dalam proses tersebut. Belum ada token toko untuk integrasi ini.

Dokumentasi publik yang dibaca belum memberikan kepastian menyeluruh tentang biaya integrasi untuk kasus LARAS. Biaya API, review, dan ketentuan kemitraan perlu dikonfirmasi; komisi penjualan marketplace merupakan biaya yang berbeda.

### Shopee

Integrasi direncanakan melalui Shopee Open Platform dengan kredensial aplikasi serta otorisasi per toko. Pendaftaran, izin, persetujuan produksi, dan implementasinya belum dijalankan dalam percakapan ini.

## Arsitektur dan pilihan model

| Komponen | Arah perencanaan |
| --- | --- |
| Antarmuka | React / Next.js untuk percakapan, tugas, persetujuan, dan hasil kerja. |
| Backend | FastAPI untuk agen, alat, validasi bisnis, autentikasi, dan kontrol akses. |
| Agen | Operator AI dan lima agen khusus; tidak perlu satu container per agen. |
| Data | PostgreSQL untuk persediaan, pemasok, pengadaan, katalog, transaksi, tugas, dan riwayat. |
| Retrieval | pgvector dan layanan retrieval sesuai kebutuhan. |
| Model pengembangan | Ollama dengan tag lokal yang telah ditemukan: `huihui_ai/qwen3-abliterated:latest`. |
| Model produksi | Target kelas 27B; identitas model, penyedia, dan konfigurasi final belum ditetapkan. |
| Hosting aplikasi | VPS dengan Docker; SumoPod merupakan kandidat dalam rancangan awal. |
| Model serving | Hosted API atau layanan GPU terpisah; pilihan produksi masih perlu evaluasi. |
| Marketplace | Tokopedia melalui jalur Partner Center yang relevan, kemudian Shopee Open Platform. |

Model huihui_ai yang terpasang di Ollama dan model Qwen pada API komersial tidak boleh dianggap identik. Nama tag `latest` juga tidak membuktikan model lokal tersebut berukuran 27B. Jika varian khusus huihui_ai wajib digunakan di produksi, ketersediaan layanan untuk bobot itu atau kebutuhan hosting GPU perlu diperiksa.

Usulan dalam diskusi adalah mengevaluasi hosted API untuk peluncuran awal apabila tersedia model yang sesuai. Ini belum merupakan keputusan final. Hosted API mengurangi pekerjaan mengoperasikan GPU, tetapi tidak menjamin latensi tertentu. GPU sewaan tetap memerlukan pengaturan kapasitas, antrean, pemantauan, dan redundansi.

Aplikasi menargetkan penggunaan di beberapa wilayah. Penempatan data pelanggan, pemilihan region model, dan kapasitas perlu dirancang secara eksplisit. Memulai dari satu region produksi merupakan usulan tahapan, bukan bukti bahwa kebutuhan multi-region sudah terpenuhi.

Pemisahan data antarperusahaan, HTTPS, pencadangan, pencatatan tindakan, dan pembatasan akses merupakan bagian rancangan produksi.

## Prioritas pengembangan

1. **Operator AI terlebih dahulu:** backend percakapan menggunakan model lokal yang sudah terpasang, instruksi peran yang jelas, dan penanganan kesalahan koneksi.
2. Menambahkan pengelolaan konteks serta pengukuran penggunaan token dan waktu respons.
3. Menghubungkan Inventory Agent ke data dan fungsi backend yang tervalidasi.
4. Membangun fondasi tugas, akun, dan persetujuan untuk pemilik serta karyawan.
5. Menambahkan Procurement Agent dan agen khusus lain secara bertahap berdasarkan alur yang diprioritaskan.
6. Memvalidasi akses Tokopedia sebelum menjanjikan publikasi marketplace secara penuh.

Penambahan Procurement ke rancangan tidak mengubah keputusan untuk memulai implementasi agen dari Operator AI. Ringkasan ini bukan audit kode; status implementasi aktual perlu dilihat di proyek.

## Estimasi anggaran historis

Angka berikut dipertahankan sebagai **asumsi simulasi dari ringkasan awal**, bukan tarif terkini atau penawaran vendor yang telah diverifikasi ulang. Rancangan awal menyebut Qwen 3.8-27B dengan asumsi US$0,50 per satu juta token input dan US$3 per satu juta token output, serta kurs Rp17.000 per US$.

Volume simulasi: 3.000 tugas per bulan. Token per tugas merupakan total seluruh panggilan agen untuk pekerjaan tersebut.

| Skenario | Input per tugas | Output per tugas | Total token per bulan | Simulasi biaya model |
| --- | ---: | ---: | ---: | ---: |
| Ringan | 5.000 | 1.000 | 18 juta | Rp280.500 |
| Sedang | 20.000 | 4.000 | 72 juta | Rp1.122.000 |
| Berat | 50.000 | 10.000 | 180 juta | Rp2.805.000 |

Anggaran skenario sedang sebelumnya mengalokasikan Rp250.000 untuk server aplikasi dan basis data, Rp100.000 untuk penyimpanan/pencadangan, dan Rp50.000 untuk domain/pemantauan. Subtotal Rp1.522.000 ditambah cadangan 25% menghasilkan Rp1.902.500 per bulan.

**Anggaran tersebut belum membuktikan kelayakan produksi B2B atau multi-region.** Belum mencakup GPU sewaan, replikasi lintas wilayah, redundansi produksi, tenaga pengembangan/pemeliharaan, pajak, embedding eksternal, atau biaya marketplace/kemitraan jika berlaku. Penambahan Procurement dapat mengubah jumlah panggilan per tugas; biaya tidak otomatis dikalikan enam hanya karena tersedia enam agen.

## Rencana evaluasi

Bandingkan pekerjaan manual dan LARAS pada kasus yang sama: waktu penyelesaian, ketepatan data, keberhasilan tugas, biaya model, dan kebutuhan intervensi manusia.

Untuk performa, ukur waktu hingga respons pertama, waktu sampai pekerjaan selesai, latensi persentil 50/95, serta kapasitas pengguna serentak. Sertakan percakapan pendek dan panjang, panggilan antaragen, serta akses dari region pelanggan.

Kasus penting mencakup data tidak lengkap, akses lintas perusahaan, stok kurang, pesanan pembelian ganda, anggaran terlampaui, keterlambatan pemasok, penerimaan sebagian/rusak, jadwal berbenturan, kegagalan API, token kedaluwarsa, serta percobaan publikasi ulang.

## Referensi

- [Dokumen rancangan LARAS](https://docs.google.com/document/d/1oVSF2YDDYQrJVrIz-BKgGQF8Fy-IU5EPQAHFdaHwAk4/edit)
- [Tarif Alibaba Cloud Model Studio](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- [Pengelolaan percakapan Qwen](https://www.alibabacloud.com/help/en/model-studio/multi-round-conversation)
- [Region Alibaba Cloud Model Studio](https://www.alibabacloud.com/help/en/model-studio/regions/)
- [TikTok Shop Partner Center](https://partner.tiktokshop.com/)
- [Alur pengembangan aplikasi Partner Center](https://partner.tiktokshop.com/docv2/page/64f198e74830a5028854bf8f)
- [Informasi migrasi integrasi Tokopedia](https://partner.tiktokshop.com/docv2/page/r1wchdjn)
- [Shopee Open Platform](https://open.shopee.com/)

Informasi platform dan biaya dalam dokumen merupakan catatan perencanaan berdasarkan percakapan. Periksa dokumentasi serta ketentuan akun yang berlaku saat implementasi.
