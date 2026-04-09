# Manual Routing Checklist

## Muc tieu

- Test routing giua 2 nhanh: Deterministic va LLM.
- Bat loi xung dot bo loc va ten tai lieu khong ton tai.
- Tick vao o [ ] sau moi test.

## Cach doc ket qua

- Xem cuoi cau tra loi, phan Thong tin xu ly.
- Gia tri can nhin:
  - Deterministic Extraction
  - Conversational Multi-hop RAG + Self-RAG
  - Xung dot bo loc
  - Khong tim thay tai lieu dich

## Trang thai filter can test

- F0: khong chon file nao trong filter.
- F1: chi chon file BAI TAP 123 - Do hoa dinh vi.pdf.
- F2: chi chon file BAI TAP 123 - Truy xuat phan cung.pdf.
- F12: chon ca F1 va F2.

## Nhom D - Deterministic

- [x] D01 | F0 | So luong bai tap cua tai lieu BAI TAP 123 - Do hoa dinh vi.pdf la bao nhieu?
- [x] D02 | F0 | Liet ke so bai tap cua tai lieu B234-LapTrinhMang (1).pdf.
- [x] D03 | F0 | Co bao nhieu bai tap trong file BAI TAP 45 - Restful API.pdf?
- [x] D04 | F0 | Tong so bai tap cua tai lieu BAI TAP 123 - Truy xuat phan cung.pdf.
- [x] D05 | F0 | How many exercises in BAI TAP 123 - Do hoa dinh vi.pdf?
- [x] D06 | F0 | Number of tasks in B234-LapTrinhMang (1).pdf.
- [x] D07 | F0 | Danh sach bai tap cua tai lieu BAI TAP 123 - Truy xuat phan cung.pdf.
- [x] D08 | F0 | Liet ke cac bai trong tai lieu BAI TAP 45 - Restful API.pdf.
- [] D09 | F0 | Chuong RESTFUL API co bao nhieu bai tap? nó bảo chỉ có 1 bài dù thực tế có 2
- [] D10 | F0 | Chuong TRUY XUAT PHAN CUNG co bao nhieu bai tap? nó bảo chỉ có 1 bài dù thực tế có 2
- [x] D11 | F0 | Chapter 2 has how many exercises?
- [x] D12 | F0 | Chuong 3 co bao nhieu bai tap?
- [x] D13 | F1 | So luong bai tap cua tai lieu nay la bao nhieu?
- [x] D14 | F2 | Liet ke so bai tap cua tai lieu nay.
- [x] D15 | F12 | So luong bai tap cua tai lieu Truy xuat phan cung?
- [x] D16 | F12 | So luong bai tap cua tai lieu Do hoa dinh vi?
- [x] D17 | F0 | Noi dung bai tap 1 cua tai lieu Do hoa dinh vi la gi?
- [x] D18 | F0 | Chi tiet bai 2 trong tai lieu Truy xuat phan cung.
- [x] D19 | F0 | De bai bai tap 3 cua B234-LapTrinhMang (1).pdf.
- [] D20 | F0 | Bai tap 1 cua Restful API co noi dung la gi? nó bảo không tìm thấy nội dung của bài tập 1
- [x] D21 | F0 | Exercise 2 content in BAI TAP 123 - Truy xuat phan cung.pdf.
- [x] D22 | F0 | Co bao nhieu phong cach kien truc trong tai lieu?
- [x] D23 | F0 | Liet ke cac phong cach kien truc trong tai lieu.
- [x] D24 | F0 | How many architecture styles are mentioned?
- [x] D25 | F0 | List architecture style mentioned in document.

## Nhom L - LLM

- [x] L01 | F0 | Tom tat muc tieu chinh cua tai lieu Do hoa dinh vi.
- [x] L02 | F0 | Giai thich ngan gon phan Google Maps duoc yeu cau nhu the nao.
- [x] L03 | F0 | So sanh noi dung chinh giua Do hoa dinh vi va Truy xuat phan cung.
- [ ] L04 | F0 | Tai lieu nao phu hop de hoc truoc cho nguoi moi, va vi sao? Không nhận diện được tài liệu đích 'nao phu hop e hoc truoc cho nguoi' trong dữ liệu đã index. Tài liệu hiện có trong index: B234-LapTrinhMang (1).pdf, BÀI TẬP 45 - Restful API.pdf, BÀI TẬP 123 - Truy xuất phần cứng.pdf, BÀI TẬP 123 - Đồ họa định vị.pdf Vui lòng nhập đúng tên tài liệu hoặc chọn lại bộ lọc tài liệu.
- [x] L05 | F0 | Hay neu cac ky nang can co de lam tot nhom bai tap nay.
- [ ] L06 | F0 | Trong tai lieu co goi y cong nghe hay thu vien nao dang chu y? Không nhận diện được tài liệu đích 'goi y cong nghe hay thu vien nao' trong dữ liệu đã index. Tài liệu hiện có trong index: B234-LapTrinhMang (1).pdf, BÀI TẬP 45 - Restful API.pdf, BÀI TẬP 123 - Truy xuất phần cứng.pdf, BÀI TẬP 123 - Đồ họa định vị.pdf Vui lòng nhập đúng tên tài liệu hoặc chọn lại bộ lọc tài liệu.
- [x] L07 | F0 | Tom tat theo 3 y quan trong nhat cua B234-LapTrinhMang (1).pdf.

== phần sau chưa test xong

- [ ] L08 | F0 | Hay viet mot ke hoach hoc 2 tuan dua tren bo tai lieu da nap.
- [ ] L09 | F0 | Muc do kho giua cac tai lieu khac nhau o diem nao?
- [ ] L10 | F0 | Tu tai lieu hien co, rut ra tieu chi danh gia bai lam tot.
- [ ] L11 | F1 | Tai lieu nay tap trung vao nang luc nao nhieu nhat?
- [ ] L12 | F2 | Neu hoc mot minh thi nen lam bai theo thu tu nao?
- [ ] L13 | F12 | Diem giao nhau ve kien thuc giua hai tai lieu dang loc la gi?
- [ ] L14 | F0 | Viet mot doan gioi thieu ngan ve bo bai tap cho sinh vien nam 2.
- [ ] L15 | F0 | Neu trien khai thanh do an, rui ro lon nhat la gi?
- [ ] L16 | F0 | Tom tat nhung phan co the tai su dung cho do an thuc te.
- [ ] L17 | F0 | Hay de xuat tieu chi cham diem cho cac bai tap nay.
- [ ] L18 | F0 | Minh nen chuan bi moi truong phat trien nhu the nao tu tai lieu?

## Nhom E - Edge cases

- [ ] E01 | F0 | Liet ke so bai tap cua tai lieu achbacjkc. | Ky vong: Khong tim thay tai lieu dich
- [ ] E02 | F0 | So luong bai tap cua file ftgyhujnc? | Ky vong: Khong tim thay tai lieu dich
- [ ] E03 | F1 | So luong bai tap cua tai lieu Truy xuat phan cung. | Ky vong: Xung dot bo loc
- [ ] E04 | F2 | Noi dung bai tap 1 cua tai lieu Do hoa dinh vi. | Ky vong: Xung dot bo loc
- [ ] E05 | F12 | Liet ke so bai tap cua tai lieu Do hoa dinh vi. | Ky vong: Deterministic va chi 1 file dich
- [ ] E06 | F0 | Cho minh noi dung bai tap 999 cua tai lieu Do hoa dinh vi. | Ky vong: Deterministic va thong bao khong tim thay bai
- [ ] E07 | F0 | Chuong ABCXYZ co bao nhieu bai tap? | Ky vong: Deterministic va thong bao khong tim thay trong chuong
- [ ] E08 | F0 | Con tai lieu do thi sao? | Ky vong: thuong la LLM + rewrite theo ngu canh
- [ ] E09 | F0 | Con bai 2 thi sao? | Ky vong: rewrite theo lich su (phu thuoc cau truoc)
- [ ] E10 | F0 | Bao nhieu kien thuc chinh trong tai lieu? | Ky vong: LLM

## Mau ghi loi de gui fix

- Test ID:
- Filter state:
- Question:
- Actual mode:
- Expected mode:
- Ket qua tom tat:
- Pass/Fail:

## Tong ket

- [ ] Da chay xong nhom D
- [ ] Da chay xong nhom L
- [ ] Da chay xong nhom E
- [ ] Da gui case Fail de fix tiep
