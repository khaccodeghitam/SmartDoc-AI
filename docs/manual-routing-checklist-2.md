# Manual Routing Checklist 2

## Muc tieu

- Test bo 2 tai lieu moi: Chapter 3.docx va Sockets_Trong_Python.docx.
- Kiem tra routing giua Deterministic va LLM.
- Kiem tra xung dot bo loc, unknown target, va follow-up.

## Cach doc ket qua

- Xem cuoi cau tra loi, phan Thong tin xu ly.
- Gia tri can nhin:
  - Deterministic Extraction
  - Deterministic Advisory
  - Conversational Multi-hop RAG + Self-RAG
  - Xung dot bo loc
  - Khong tim thay tai lieu dich

## Trang thai filter can test

- F0: khong chon file nao trong filter.
- F1: chi chon file Chapter 3.docx.
- F2: chi chon file Sockets_Trong_Python.docx.
- F12: chon ca 2 file tren.

## Nhom D - Deterministic

- [x] D01 | F0 | Co bao nhieu phong cach kien truc trong Chapter 3.docx?
- [x] D02 | F0 | Liet ke cac phong cach kien truc trong Chapter 3.docx.
- [x] D03 | F0 | So luong architecture style trong Chapter 3.docx la bao nhieu?
- [x] D04 | F0 | Chuong 3 co bao nhieu phong cach kien truc?
- [x] D05 | F1 | Tai lieu nay co bao nhieu phong cach kien truc?
- [x] D06 | F1 | Liet ke architecture style trong tai lieu nay.
- [x] D07 | F0 | Trong Sockets_Trong_Python.docx co bao nhieu vi du code?
- [x] D08 | F2 | Tai lieu nay co bao nhieu doan code server/client?
- [x] D09 | F0 | Co bao nhieu buoc tao server socket trong tai lieu Sockets_Trong_Python.docx?
- [x] D10 | F0 | Chuong sockets co bao nhieu thanh phan client-server duoc mo ta?

## Nhom L - LLM

- [x] L01 | F0 | Tai lieu nao phu hop de hoc truoc cho nguoi moi, va vi sao?
- [x] L02 | F0 | Trong tai lieu co goi y cong nghe hay thu vien nao dang chu y?
- [x] L03 | F0 | Tom tat 3 y chinh cua Chapter 3.docx.
- [x] L04 | F0 | Tom tat 3 y chinh cua Sockets_Trong_Python.docx.
- [x] L05 | F0 | So sanh ngan gon tu duy kien truc he thong va lap trinh socket.
- [x] L06 | F0 | Neu lam do an chat TCP, nen doc phan nao truoc?
- [x] L07 | F1 | Tu tai lieu nay, de xuat tieu chi danh gia bai lam tot.
- [x] L08 | F2 | Tu tai lieu nay, de xuat lo trinh hoc 5 buoi.
- [x] L09 | F12 | Diem giao nhau ve kien thuc giua hai tai lieu dang loc la gi?
- [x] L10 | F0 | Rui ro lon nhat khi implement server-client theo tai lieu la gi?

## Nhom E - Edge cases

- [x] E01 | F0 | Liet ke phong cach kien truc cua tai lieu abcxyz. | Ky vong: Khong tim thay tai lieu dich
- [x] E02 | F0 | So luong bai tap cua file qwerty123? | Ky vong: Khong tim thay tai lieu dich
- [x] E03 | F1 | Liet ke code socket trong tai lieu Sockets_Trong_Python.docx. | Ky vong: Xung dot bo loc
- [x] E04 | F2 | Liet ke architecture style trong Chapter 3.docx. | Ky vong: Xung dot bo loc
- [x] E05 | F12 | Tai lieu nao phu hop hoc truoc cho nguoi moi? | Ky vong: Deterministic Advisory
- [x] E06 | F0 | Con tai lieu do thi sao? | Ky vong: LLM + follow-up rewrite
- [x] E07 | F0 | Con phan client thi sao? | Ky vong: LLM + follow-up rewrite
- [x] E08 | F0 | Chuong ABCXYZ co bao nhieu phong cach kien truc? | Ky vong: Deterministic va thong bao khong tim thay

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
