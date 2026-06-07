# Notification System Design

This document covers the architectural and system design choices for the Campus Notifications Microservice across Stages 1 to 6.

## Stage 1: REST API Design

### 1. `GET /api/v1/notifications`
Fetches a list of notifications for the logged-in user.

**Headers:**
- `Authorization`: `Bearer <token>`

**Response (200 OK):**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "Placement | Result | Event",
      "message": "Notification content",
      "isRead": false,
      "createdAt": "2026-06-07T12:00:00Z"
    }
  ],
  "pagination": { "nextCursor": "abc" }
}
```

### 2. `PATCH /api/v1/notifications/:id/read`
Marks a specific notification as read.

**Headers:**
- `Authorization`: `Bearer <token>`

**Response (200 OK):**
```json
{ "success": true, "message": "Notification marked as read" }
```

### 3. `PATCH /api/v1/notifications/read-all`
Marks all unread notifications as read for the user.

**Response (200 OK):**
```json
{ "success": true, "message": "All notifications marked as read" }
```

### Real-Time Mechanism
For real-time delivery without overwhelming the server with polling, we will use **WebSockets** or **Server-Sent Events (SSE)**. SSE is typically sufficient for unidirectional server-to-client notifications and is lighter than WebSockets. Clients subscribe to `/api/v1/notifications/stream`.

---

## Stage 2: Database Storage Choice & Schema

### Storage Choice
**PostgreSQL** (Relational Database) is highly suitable. Notifications have a structured schema and require reliable ACID transactions (e.g., ensuring read statuses are accurate). For caching and real-time delivery queuing, we can use **Redis**.

### DB Schema (PostgreSQL)
```sql
CREATE TYPE notification_type AS ENUM ('Event', 'Result', 'Placement');

CREATE TABLE users (
    studentID INT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255)
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    studentID INT REFERENCES users(studentID),
    notificationType notification_type,
    message TEXT,
    isRead BOOLEAN DEFAULT false,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Potential Problems with Data Volume & Solutions
- **Problem:** As volume increases, the `notifications` table will grow exponentially, slowing down queries.
- **Solution 1 (Archiving):** Move notifications older than 30 days to cold storage (e.g., AWS S3 or a secondary DB).
- **Solution 2 (Partitioning):** Partition the table by `createdAt` (e.g., monthly partitions) so the working set fits into memory.

---

## Stage 3: Slow Query Analysis & Indexing

The query:
```sql
SELECT * FROM notifications 
WHERE studentID = 1042 AND isRead = false 
ORDER BY createdAt DESC;
```

### Why is it slow?
It is slow because without an index, the DB has to perform a full table scan across 5,000,000 rows to find records matching the criteria. 

### Is adding indexes on *every* column effective?
**No.** Adding indexes on every column significantly increases the storage footprint and slows down write operations (`INSERT`, `UPDATE`) because every index must be updated synchronously.

### What to change?
We should add a **Composite Index** specifically targeted at the slow query:
```sql
CREATE INDEX idx_student_read_created 
ON notifications(studentID, isRead, createdAt DESC);
```
**Computation Cost:** Minimal impact on writes (since only one B-Tree index is updated), but massive speedup (O(log N)) for read queries.

### Query for Placement Notifications in the last 7 days:
```sql
SELECT * FROM notifications 
WHERE notificationType = 'Placement' 
  AND createdAt >= NOW() - INTERVAL '7 days';
```

---

## Stage 4: Performance Improvements

**Problem:** Fetching notifications on each page load overwhelms the database.
**Solution:** 
1. **Caching Layer:** Use **Redis** to cache the unread notification count and the first page of notifications for active users. Update the cache invalidation asynchronously on new notification inserts.
2. **Push over Pull:** Replace HTTP polling with **Server-Sent Events (SSE)**. The frontend maintains a single open connection, and the server pushes new notifications instantly. This completely eliminates the DB reads from continuous polling.

**Tradeoffs:**
- *SSE vs Polling:* SSE is stateful and requires keeping connections open, which consumes RAM on the load balancers/servers, but it saves immense DB CPU load compared to polling.

---

## Stage 5: Bulk Notification Redesign

The original pseudocode fails sequentially and synchronously, causing timeouts and partial failures (200 students missed).

**Shortcomings observed:**
1. Processing 50,000 emails synchronously will timeout the API request.
2. If `send_email` throws an error, the loop breaks or fails, and DB inserts don't happen.
3. Tight coupling between DB insertion and external API calls.

**Redesign Strategy:**
We should use the **Transactional Outbox Pattern** along with an asynchronous Message Queue (e.g., RabbitMQ, Kafka, or AWS SQS/SNS). We insert the notifications into the DB *first* to guarantee they are recorded, and then dispatch jobs to background workers to handle the slow/flaky Email API.

**Revised Pseudocode:**

```python
function notify_all(student_ids: array, message: string):
    # 1. Bulk Insert into DB for all users (Fast)
    bulk_save_to_db(student_ids, message)
    
    # 2. Push to real-time WebSockets/SSE mechanism (Fast)
    push_to_app_bulk(student_ids, message)
    
    # 3. Queue email jobs to a message broker (Asynchronous)
    for student_id in student_ids:
        enqueue_message_to_queue(student_id, message)

# Worker Process (running independently):
function process_email_queue(job):
    try:
        send_email(job.student_id, job.message)
    except EmailAPIError:
        # Automatically retried by the queue system later
        job.retry_with_backoff()
```

---

## Stage 6: Priority Inbox Implementation

**Approach:**
To maintain the Top 10 priority notifications efficiently as new notifications stream in, we use a **Min-Heap (Priority Queue)** constrained to a maximum size of 10. 

**Logic:**
1. Assign numerical weights to the types: `Placement (3) > Result (2) > Event (1)`.
2. As notifications are fetched from the API, we create a tuple `(Weight, Timestamp, NotificationObject)`.
3. We push the tuple into a Min-Heap.
4. If the heap size exceeds 10, we compare the new notification with the smallest element (the root of the Min-Heap).
5. If the new notification has a higher priority/recency than the root, we `pop` the root and `push` the new notification. 
6. This guarantees that the heap always retains exactly the 10 highest-priority elements. Time complexity for inserting `N` items into a size `K` heap is `O(N log K)`, which is extremely efficient for memory and CPU.

The code implementation for this is located in the `notification_app_be/priority_inbox.py` file.
