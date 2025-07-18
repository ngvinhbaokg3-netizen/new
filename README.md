# KLTTS AI Clone - Text-to-Speech Tiếng Việt

Ứng dụng chuyển văn bản thành giọng nói tiếng Việt với tích hợp ElevenLabs và tính năng tải xuống MP3.

## 🎯 Tính năng

- ✅ **Giọng nói hệ thống**: Sử dụng SpeechSynthesis API của trình duyệt
- ✅ **Giọng nói ElevenLabs**: 22 giọng nói chất lượng cao (cần API Key)
- ✅ **Tải xuống MP3**: Lưu file audio từ ElevenLabs
- ✅ **Giao diện tiếng Việt**: Hoàn toàn bằng tiếng Việt
- ✅ **Responsive**: Tương thích mọi thiết bị
- ✅ **Phím tắt**: Ctrl+Enter (phát), Escape (dừng), Ctrl+D (tải xuống)

## 🚀 Triển khai

### 1. Deploy lên Vercel (Khuyến nghị)

1. Fork repository này
2. Truy cập [vercel.com](https://vercel.com)
3. Đăng nhập và chọn "New Project"
4. Import repository từ GitHub
5. Deploy tự động

### 2. Deploy lên Netlify

1. Fork repository này
2. Truy cập [netlify.com](https://netlify.com)
3. Chọn "New site from Git"
4. Kết nối với GitHub và chọn repository
5. Deploy settings:
   - Build command: (để trống)
   - Publish directory: `/`

### 3. Deploy lên GitHub Pages

1. Fork repository này
2. Vào Settings > Pages
3. Source: Deploy from a branch
4. Branch: main / (root)
5. Save

## 🔧 Chạy Local

```bash
# Clone repository
git clone <repository-url>
cd kltts-ai-clone

# Chạy server local
python3 -m http.server 8000
# hoặc
npx serve .

# Mở trình duyệt
http://localhost:8000
```

## 📁 Cấu trúc File

```
/
├── index.html          # Trang chính
├── css/
│   └── style.css      # Styling
├── js/
│   └── script.js      # Logic ứng dụng
├── voices.json        # Cấu hình giọng ElevenLabs
├── vercel.json        # Cấu hình Vercel
└── README.md          # Hướng dẫn
```

## 🎭 Sử dụng ElevenLabs

1. Đăng ký tài khoản tại [elevenlabs.io](https://elevenlabs.io)
2. Lấy API Key từ Profile > API Keys
3. Chọn giọng ElevenLabs trong dropdown
4. Nhập API Key khi được yêu cầu
5. Tạo giọng nói và tải xuống MP3

## 🔒 Bảo mật

- API Key chỉ lưu tạm trong phiên làm việc
- Không gửi dữ liệu đến server (trừ ElevenLabs API)
- Tất cả xử lý diễn ra trên client-side

## 📱 Tương thích

- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers

## 🎨 Tùy chỉnh

Bạn có thể tùy chỉnh:
- Thêm giọng nói trong `voices.json`
- Thay đổi giao diện trong `css/style.css`
- Mở rộng tính năng trong `js/script.js`

## 📄 License

MIT License - Sử dụng tự do cho mục đích cá nhân và thương mại.

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

---

**Lưu ý**: Đây là bản clone của KLTTS AI với mục đích học tập và sử dụng cá nhân.
