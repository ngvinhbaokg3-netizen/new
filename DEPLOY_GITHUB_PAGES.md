# 🚀 Hướng dẫn Deploy lên GitHub Pages

## Bước 1: Tạo Repository trên GitHub

1. Truy cập [github.com](https://github.com)
2. Đăng nhập vào tài khoản GitHub của bạn
3. Click nút **"New"** hoặc **"+"** > **"New repository"**
4. Đặt tên repository: `kltts-ai-clone` (hoặc tên bạn muốn)
5. Chọn **Public** (bắt buộc cho GitHub Pages miễn phí)
6. **KHÔNG** tick vào "Add a README file"
7. Click **"Create repository"**

## Bước 2: Upload Code lên GitHub

### Cách A: Sử dụng Git Command Line
```bash
# Khởi tạo git trong thư mục dự án
git init

# Thêm tất cả files
git add .

# Commit đầu tiên
git commit -m "Initial commit - KLTTS AI Clone with MP3 download"

# Thêm remote origin (thay YOUR_USERNAME và YOUR_REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push code lên GitHub
git branch -M main
git push -u origin main
```

### Cách B: Upload trực tiếp trên GitHub
1. Vào repository vừa tạo
2. Click **"uploading an existing file"**
3. Kéo thả tất cả files trong thư mục dự án:
   - `index.html`
   - `package.json`
   - `README.md`
   - `vercel.json`
   - `voices.json`
   - `.gitignore`
   - Thư mục `css/` (với file `style.css`)
   - Thư mục `js/` (với file `script.js`)
4. Commit message: "Initial commit - KLTTS AI Clone"
5. Click **"Commit changes"**

## Bước 3: Kích hoạt GitHub Pages

1. Trong repository, click tab **"Settings"**
2. Scroll xuống phần **"Pages"** (bên trái sidebar)
3. Trong **"Source"**, chọn **"Deploy from a branch"**
4. **Branch**: chọn **"main"**
5. **Folder**: chọn **"/ (root)"**
6. Click **"Save"**

## Bước 4: Truy cập Website

- GitHub sẽ build và deploy tự động (2-5 phút)
- URL sẽ là: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`
- Ví dụ: `https://johndoe.github.io/kltts-ai-clone/`

## Bước 5: Kiểm tra Deploy

1. Đợi vài phút để GitHub build
2. Refresh trang Settings > Pages
3. Sẽ thấy thông báo: "Your site is published at https://..."
4. Click vào link để kiểm tra website

## 🔧 Cập nhật Website

Khi muốn cập nhật:
1. Chỉnh sửa files trên GitHub hoặc push code mới
2. GitHub Pages sẽ tự động rebuild và deploy

## ⚠️ Lưu ý quan trọng

1. **Repository phải là Public** (GitHub Pages miễn phí chỉ cho public repo)
2. **File chính phải là `index.html`** (đã có sẵn)
3. **CORS**: ElevenLabs API có thể bị chặn CORS trên một số domain, nhưng thường hoạt động tốt với GitHub Pages
4. **HTTPS**: GitHub Pages tự động có SSL certificate

## 🎯 Kết quả

Sau khi deploy thành công, bạn sẽ có:
- ✅ Website công khai trên internet
- ✅ URL dạng: `https://username.github.io/repo-name/`
- ✅ Tự động cập nhật khi push code mới
- ✅ Miễn phí hoàn toàn
- ✅ Hỗ trợ HTTPS
- ✅ Tốc độ tải nhanh

## 🆘 Troubleshooting

**Nếu website không hiển thị:**
1. Kiểm tra Settings > Pages có hiển thị URL không
2. Đợi 5-10 phút để GitHub build xong
3. Kiểm tra file `index.html` có ở root directory không
4. Clear cache trình duyệt và thử lại

**Nếu ElevenLabs không hoạt động:**
- Đây là do CORS policy, bạn có thể thử deploy lên Vercel hoặc Netlify thay thế
