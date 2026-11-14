# SQL выборки по StPlatform
База:

users содержит id, фио, роль (студент или преподаватель).

assignment содержит задания, у каждого id, номер пары и название.

submission, где указано кто сдал, по какому заданию, когда и с каким статусом.

**a) Все сдачи студента по фамилии**

Фамилия - это параметр, который подставляется в запрос. Первый в списке студент, у которого еще и несколько сдач - Иванов, поэтому запрос пишем для него.

Берем submissions, добавляем к ней users по student_id, чтобы появилось фио, и assignment по assignment_id, чтобы появилось название задания. В условии пробел, чтобы не попала в выборку Иванова Мария.

SELECT u.full_name, a.pair_number, a.title, s.created_at, s.status

FROM submissions s

JOIN users u      ON u.id = s.student_id

JOIN assignment a ON a.id = s.assignment_id

WHERE u.full_name LIKE 'Иванов %'

ORDER BY s.created_at;

Вышло 3 строки, где указаны 2 сдачи по шестому дз и одна по седьмому.

**b) Сколько сдач пришло на каждое задание**

Сначала сделала обычный JOIN и сгруппировала по заданию, но заметила, что  в ответе только два задания, а их три. Поняла, что обычный JOIN выкиывает задание, которое еще никто не сдал, поэтому заменила на LEFT JOIN, где задание остается, даже если сдач нет, и стала считать через COUNT.

SELECT a.pair_number, a.title, COUNT(s.id) AS submissions_count

FROM assignment a

LEFT JOIN submissions s ON s.assignment_id = a.id

GROUP BY a.id, a.pair_number, a.title

ORDER BY a.pair_number;

Получилось 6 для дз №6, 3 для дз №7, 0 для дз №8

**c) Студенты, не сдавшие ни одной работы**

Взяла студентов и проверила, что у них нет ни одной сдачи, с фильтром по роли, чтобы преподаватель не попал

SELECT u.full_name, u.group_name, u.email

FROM users u

WHERE u.role = 'STUDENT'

  AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.student_id = u.id)

ORDER BY u.group_name, u.full_name;

В итоге остался один Игорь Морозов из ПАД-2
