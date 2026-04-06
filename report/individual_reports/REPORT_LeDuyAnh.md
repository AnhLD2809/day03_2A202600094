# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Duy Anh
- **Student ID**: 2A202600094
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/agent/agent.py`, `main.py`
- **Code Highlights**: 
action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\((.*?)\)", response_text)

if action_match:
    tool_name = action_match.group(1).strip()
    tool_args = action_match.group(2).strip()
    observation = self._execute_tool(tool_name, tool_args)
    context += f"\nObservation: {observation}"
else:
    error_msg = "Error: Please use the format 'Action: tool_name(args)' or provide a 'Final Answer:'."
    context += f"\nObservation: {error_msg}"
- **Documentation**: Hệ thống khởi tạo vòng lặp nhận đầu vào user_input và lưu vào biến context. Tại mỗi bước, LLM sinh ra suy luận (Thought) và yêu cầu gọi công cụ (Action). Mã nguồn sử dụng Regex để trích xuất tên công cụ và tham số, tiến hành gọi hàm qua _execute_tool(), sau đó đẩy kết quả (Observation) ngược lại vào context để LLM tiếp tục xử lý cho tới khi đưa ra Final Answer hoặc đạt giới hạn max_steps.
---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Mô tả vấn đề: Agent bỏ qua yêu cầu tạo lịch học chi tiết của người dùng. Mặc dù đã tìm kiếm thành công tài liệu Machine Learning và tính toán được số ngày còn lại (26 ngày), Agent lại kết thúc chu trình xử lý (AGENT_END) ngay lập tức mà không gọi công cụ lập kế hoạch để phân bổ thời gian học (2 giờ/ngày).
- **Log Source**:
{"timestamp": "2026-04-06T10:23:55.378735", "event": "AGENT_START", "data": {"input": "I want to apply to the university's Artificial Intelligence Lab (AI Lab) at the end of this month. Could you help me find some basic Machine Learning study materials and schedule a 2-hour daily practical study session from now until the exam?", "model": "gemini-2.5-flash"}}
{"timestamp": "2026-04-06T10:24:00.836122", "event": "TOOL_CALL", "data": {"tool": "search", "args": "\"basic machine learning study materials for AI lab admission\"", "result": "1.  Introduction to Machine Learning: Definition, types (supervised, unsupervised, reinforcement), common applications.\n2.  Fundamental Concepts: Data types, features, labels, training vs. testing data, basic statistics for ML.\n3.  Supervised Learning Basics: Linear Regression (concept, cost function), Logistic Regression (binary classification), introduction to Decision Trees.\n4.  Unsupervised Learning Basics: K-Means Clustering (concept, use cases).\n5.  Model Evaluation & Improvement: Overfitting/underfitting, cross-validation, basic performance metrics (accuracy, precision, recall)."}}
{"timestamp": "2026-04-06T10:24:04.206446", "event": "TOOL_CALL", "data": {"tool": "calculate_date", "args": "\"end of this month\"", "result": "26"}}
{"timestamp": "2026-04-06T10:24:10.137692", "event": "AGENT_END", "data": {"steps": 3, "status": "success"}}
- **Diagnosis**: System prompt thiếu các chỉ dẫn tường minh về quy trình (workflow). Khi không có ràng buộc chặt chẽ, LLM tự đánh giá rằng việc lấy được thông tin tài liệu và mốc thời gian là đã đủ để trả lời câu hỏi, dẫn đến ảo giác "hoàn thành nhiệm vụ" và bỏ qua bước phân bổ lịch trình.
- **Solution**: Tái cấu trúc lại System Prompt bằng cách bổ sung một Required Workflow (Quy trình làm việc bắt buộc) với các bước được đánh số thứ tự rõ ràng. Đặc biệt, thêm một quy tắc hành vi (Behavior Rule) nhấn mạnh: "Ngay sau khi nhận được Observation từ calculate_date, Thought tiếp theo phải tập trung vào việc lên kế hoạch và Action tiếp theo bắt buộc phải là task_planner."

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: How did the `Thought` block help the agent compared to a direct Chatbot answer?
Trả lời: Khối Thought đóng vai trò như "bộ nhớ làm việc" và "bản kế hoạch chiến lược" của Agent:
    
    - Chia nhỏ vấn đề: Khác với Chatbot thường nhảy ngay đến kết luận, Thought cho phép Agent chia nhỏ yêu cầu phức tạp thành các mục tiêu phụ tuần tự.
    
    - Tự điều chỉnh: Đây là không gian để Agent tự nhận xét. Nếu một hành động trước đó thất bại, Agent sẽ ghi nhận lỗi trong phần Thought và thay đổi chiến thuật trước khi thực hiện bước tiếp theo.
    
    - Giữ vững ngữ cảnh: Nó đảm bảo Agent duy trì được "luồng logic", giúp nó ghi nhớ tại sao mình lại tìm kiếm một dữ liệu cụ thể trong một quy trình gồm nhiều bước.

2.  **Reliability**: In which cases did the Agent actually perform *worse* than the Chatbot?
Trả lời: Mặc dù mạnh mẽ hơn, Agent lại dễ gặp lỗi trong các tình huống cụ thể:

    - Vòng lặp vô hạn: Agent có thể bị kẹt trong "vòng lặp lập luận", nơi nó liên tục thử một hành động không thành công hoặc phân tích quá mức một câu hỏi đơn giản mà Chatbot có thể trả lời ngay lập tức bằng kiến thức sẵn có.

    - Nhạy cảm với công cụ: Nếu kết quả từ công cụ (Observation) bị nhiễu hoặc định dạng sai, Agent có thể "ảo tưởng" ra một hướng đi sai lệch dựa trên dữ liệu lỗi đó.

    - Chi phí và độ trễ: Với các tác vụ viết lách sáng tạo hoặc trò chuyện thông thường, quy trình ReAct gây tốn kém tài nguyên và tạo độ trễ không cần thiết mà không làm tăng chất lượng câu trả lời.

3.  **Observation**: How did the environment feedback (observations) influence the next steps?
Trả lời: Observation chính là "bản kiểm chứng thực tế" quyết định quỹ đạo của Agent:

    - Logic nhánh: Kết quả quan sát thường đóng vai trò là ngã rẽ. Ví dụ: nếu công cụ tìm kiếm trả về "Không có kết quả", phần Observation này buộc phần Thought tiếp theo phải mở rộng từ khóa hoặc thử một công cụ khác.

    - Tiêu chuẩn dừng: Observation cho Agent biết khi nào đã có đủ thông tin. Khi kết quả quan sát chứa "mảnh ghép cuối cùng", Agent sẽ chuyển từ trạng thái "Hành động" sang "Câu trả lời cuối cùng".

    - Xử lý lỗi: Nếu một công cụ trả về thông báo lỗi, chính Observation đó sẽ trở thành động lực chính cho bước Thought tiếp theo, chuyển mục tiêu của Agent từ "trả lời người dùng" sang "khắc phục lỗi hệ thống".
---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: 
    - Cơ chế xếp hàng không đồng bộ (Asynchronous Queues): Sử dụng các hệ thống như Celery hoặc Redis để xử lý các cuộc gọi công cụ (tool calls) nặng, giúp hệ thống không bị tắc nghẽn khi có nhiều người dùng đồng thời.

    - Microservices cho Công cụ: Tách biệt mỗi công cụ (tool) thành một microservice riêng biệt, cho phép mở rộng độc lập các công cụ tài nguyên nặng (như xử lý video/hình ảnh) mà không ảnh hưởng đến logic cốt lõi của Agent.

- **Safety**: 
    - LLM Giám sát (Supervisor LLM): Triển khai một mô hình ngôn ngữ thứ hai chuyên trách việc kiểm duyệt (audit). Mô hình này sẽ kiểm tra kế hoạch trong Thought và kết quả của Action để đảm bảo Agent không vi phạm chính sách bảo mật hoặc thực hiện các hành động gây hại trước khi chúng được thực hiện thực tế.

    - Human-in-the-loop (Con người kiểm soát): Thiết lập các rào chắn đối với các hành động nhạy cảm (như chuyển tiền hoặc xóa dữ liệu), yêu cầu sự phê duyệt trực tiếp của con người thông qua giao diện quản trị.
- **Performance**: 
    - Vector DB cho việc truy xuất công cụ (Tool Retrieval): Trong một hệ thống có hàng trăm công cụ, thay vì đưa toàn bộ mô tả công cụ vào prompt (gây tốn token), ta sẽ sử dụng Vector Database để tìm kiếm và chỉ cung cấp những công cụ phù hợp nhất cho ngữ cảnh hiện tại của Agent.

    - Cơ chế lưu bộ nhớ đệm (Caching): Lưu trữ kết quả của các bước lập luận và quan sát phổ biến. Nếu Agent gặp lại một tác vụ tương tự, nó có thể tái sử dụng "lộ trình suy nghĩ" cũ thay vì phải chạy lại toàn bộ quy trình ReAct từ đầu.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
