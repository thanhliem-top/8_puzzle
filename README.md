# AI Search Algorithms Visualization for 8 Puzzle

Ứng dụng mô phỏng thuật toán tìm kiếm AI cho trò chơi **8 Puzzle**, viết 100% bằng Python và giữ đúng ràng buộc: **chỉ có một file source Python duy nhất**.

Project được thiết kế như một đồ án đại học hoàn chỉnh: có giao diện tối hiện đại, chạy từng bước, giải thích quyết định của thuật toán, thống kê hiệu năng, cây tìm kiếm, pseudocode, chế độ so sánh và các mô phỏng giáo dục cho nhóm thuật toán không trực tiếp phù hợp với 8 Puzzle chuẩn.

---

## Demo

Chạy ứng dụng:

```bash
python ai_search_8_puzzle.py
```

Chạy kiểm thử nhanh phần thuật toán:

```bash
python ai_search_8_puzzle.py --self-test
```

Giao diện chính gồm:

```text
+--------------------------------------------------------------------------------+
| Toolbar: Group | Algorithm | Heuristic | Goal Preset | Speed                  |
| Actions: Reset | Shuffle | Undo | Redo | Step | Auto Run | Pause | Export |
+-----------------------------+------------------------------+-------------------+
| Puzzle Board                | Search Tree                  | Statistics        |
| Initial State 3x3           | Current / Frontier / Solved  | Cost Details      |
| Goal State 3x3              | Zoom In / Zoom Out           | Open / Closed     |
+-----------------------------+------------------------------+-------------------+
| Pseudocode                  | AI Explanation               | Console Log       |
+--------------------------------------------------------------------------------+
```

Các tab:

- **Solver**: chọn nhóm thuật toán, chọn thuật toán trong nhóm, rồi chạy từng bước hoặc tự động.
- **Compare**: chạy nhiều thuật toán trên cùng trạng thái và so sánh kết quả.
- **Educational Demo**: mô phỏng khái niệm cho Complex Environments, CSP và Adversarial Search.

---

## Cấu Trúc Project

```text
ai-search-8-puzzle/
├── ai_search_8_puzzle.py   # Toàn bộ source code Python duy nhất
└── README.md               # Tài liệu hướng dẫn
```

Không có package phụ, không chia module, không cần cài thư viện ngoài.

---

## Thuật Toán Hỗ Trợ

### Uninformed Search

- Breadth First Search
- Depth First Search
- Depth Limited Search
- Iterative Deepening Search
- Uniform Cost Search

### Informed Search

- Greedy Best First Search
- A*
- Heuristic Generator:
  - Manhattan Distance
  - Misplaced Tiles
  - Euclidean Distance

### Local Search

- Hill Climbing
- Local Beam Search
- Simulated Annealing

### Searching in Complex Environments

- AND-OR Search
- No Observation Search
- Partially Observable Search
- Online Search

Nhóm này được trình bày bằng **Educational Demo**, vì 8 Puzzle chuẩn là bài toán single-agent, deterministic, fully observable.

### Constraint Satisfaction Problems

- Constraint Propagation
- Path Consistency
- Global Constraints
- Backtracking Search
- Min Conflicts
- Constraint Graph

Nhóm CSP dùng trạng thái 8 Puzzle để minh họa biến, miền giá trị, ràng buộc `all-different` và quan hệ nhất quán.

### Adversarial Search

- Minimax
- Alpha Beta
- Expectimax

8 Puzzle chuẩn không phải trò chơi đối kháng, nên nhóm này được thiết kế ở dạng trình diễn giáo dục có giải thích rõ.

---

## Chức Năng Chính

- Sinh trạng thái ngẫu nhiên bằng shuffle hợp lệ.
- Nhập trạng thái thủ công.
- Nhập hoặc chọn trạng thái đích tùy ý.
- Kiểm tra trạng thái hợp lệ.
- Kiểm tra solvable.
- Reset, Shuffle, Undo, Redo.
- Step, Auto Run, Pause, Resume, Stop.
- Điều chỉnh tốc độ chạy.
- Chọn nhóm thuật toán, thuật toán, heuristic và goal state.
- Hiển thị thời gian chạy, node, frontier, explored, depth, cost.
- Hiển thị `g(n)`, `h(n)`, `f(n)=g(n)+h(n)`.
- Hiển thị search tree với node hiện tại, frontier, explored, solution.
- Hiển thị pseudocode và highlight dòng đang thực thi.
- Giải thích AI cho từng bước.
- So sánh thuật toán bằng bảng.
- Export kết quả ra JSON hoặc CSV.

---

## Hướng Dẫn Sử Dụng

1. Mở ứng dụng bằng `python ai_search_8_puzzle.py`.
2. Nhập trạng thái 8 Puzzle hoặc nhấn **Shuffle**.
3. Chọn nhóm trong combobox **Group** để danh sách thuật toán không bị trộn chung.
4. Chọn thuật toán trong combobox **Algorithm** thuộc nhóm đó.
5. Chọn heuristic nếu dùng thuật toán informed/local search.
6. Chọn **Goal Preset** hoặc nhập trực tiếp 9 ô trong bảng **Goal State**, sau đó nhấn **Apply Goal**.
7. Nhấn **Step** để chạy từng bước.
8. Nhấn **Auto Run** để chạy tự động.
9. Dùng **Pause**, **Resume**, **Stop** để điều khiển quá trình.
10. Quan sát:
   - Puzzle Board
   - Search Tree
   - Statistics
   - Pseudocode
   - AI Explanation
   - Console Log
11. Nhấn **Export** để lưu kết quả.

---

## Chạy Từng Bước Thuật Toán

Mỗi lần nhấn **Step**, ứng dụng cập nhật đầy đủ:

- Current Node
- Parent
- Children
- Frontier
- Explored
- Visited
- Depth
- Cost
- Move
- Action
- Open List
- Closed List
- Stack / Queue / Priority Queue theo thuật toán
- Node được chọn
- Node vừa mở rộng
- Node bị loại bỏ
- Lý do node được chọn

Ví dụ:

- BFS giải thích bằng Queue.
- DFS giải thích bằng Stack.
- UCS giải thích bằng `g(n)`.
- Greedy giải thích bằng `h(n)`.
- A* giải thích bằng `f(n)=g(n)+h(n)`.

---

## So Sánh Thuật Toán

Tab **Compare** cho phép chạy nhiều thuật toán trên cùng initial state và goal state hiện tại, bao gồm cả goal nhập tay.

Các checkbox trong Compare cũng được chia theo nhóm **Uninformed Search**, **Informed Search** và **Local Search** để dễ đọc hơn.

Bảng so sánh gồm:

- Time
- Memory
- Nodes
- Solution Length
- Optimal
- Complete
- Complexity
- Status

Ứng dụng cũng tạo nhận xét ngắn về thuật toán nhanh nhất và thuật toán mở rộng ít node nhất trong nhóm chạy thành công.

---

## Thiết Kế Kỹ Thuật

Toàn bộ source nằm trong `ai_search_8_puzzle.py`, nhưng được tổ chức bằng class:

- `PuzzleState`: biểu diễn trạng thái 8 Puzzle.
- `PuzzleValidator`: kiểm tra hợp lệ và solvable.
- `HeuristicManager`: tính heuristic.
- `SearchNode`: node trong cây tìm kiếm.
- `StepSnapshot`: dữ liệu một bước mô phỏng.
- `GraphSearchAlgorithm`: BFS, DFS, DLS, UCS, Greedy, A*.
- `IterativeDeepeningAlgorithm`: IDS.
- `LocalSearchAlgorithm`: Hill Climbing, Beam, Simulated Annealing.
- `EducationalAlgorithm`: mô phỏng giáo dục cho CSP, adversarial và complex environments.
- `SearchEngine`: quản lý Step, Undo, Redo và export.
- `VisualizationApp`: giao diện chính.

---

## Kiểm Thử

Lệnh:

```bash
python ai_search_8_puzzle.py --self-test
```

Self-test kiểm tra:

- Tính hợp lệ của trạng thái.
- Tính solvable.
- Manhattan Distance.
- Misplaced Tiles.
- BFS giải được puzzle dễ.
- UCS giải được puzzle dễ.
- A* giải được puzzle dễ.
- Local Search chạy được.
- Educational Demo chạy được.

---

## Các Cải Tiến Tương Lai

- Animation mượt hơn cho từng tile.
- Quiz mode để sinh viên đoán node tiếp theo.
- Lưu lịch sử chạy thuật toán.
- Xuất báo cáo PDF.
- Biểu đồ so sánh thời gian, node và bộ nhớ.
- Heuristic nâng cao như Linear Conflict.
- Replay toàn bộ quá trình giải.
- Bộ unit test riêng cho từng thuật toán.
- Phiên bản web app trong tương lai, nếu không còn ràng buộc 100% Python một file.

---

## Ghi Chú Học Thuật

Project cố tình phân biệt rõ hai nhóm:

- **Thuật toán giải trực tiếp 8 Puzzle**: BFS, DFS, DLS, IDS, UCS, Greedy, A*, Hill Climbing, Beam, Simulated Annealing.
- **Thuật toán trình diễn giáo dục**: AND-OR, No Observation, Partially Observable, Online, CSP, Minimax, Alpha Beta, Expectimax.

Cách thiết kế này tránh việc áp dụng sai bản chất thuật toán, đồng thời vẫn giúp sinh viên hiểu được ý tưởng AI Search rộng hơn thông qua cùng một đối tượng trực quan là 8 Puzzle.
