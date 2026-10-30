# Карта зависимостей StPlatform
Сценарий: сдача домашней работы

Я посмотрела структуру проекта и выбрала для разбора процесс сдачи домашней работы. Данный сценарий затрагивает две основные папки - api и submission.

В api находится ApiSubmissionController.submit. Он принимает запрос от студента на сдачу работы. Он достаёт студента через UserService.byId И передает в SubmissionService.submit. 

В submission находятся SubmissionService.submit и SubmissionRepository, отвечающие за обработку и сохранение работы.

Основная цепочка выглядит следующим образом:
ApiSubmissionController.submit() -> SubmissionService.submit() -> SubmissionRepository.save().

То есть сначала контроллер получает запрос отстудента и передает его сервису, затем сервис проверяет данные, можно ли сдать работу, не истек ли срок сдачи и не отправлял ли студент её раньше. А репозиторий после проверок сохраняет результат. После отправки может запускаться проверка работы.

Зависимости идут сверху вниз. Контроллер обраается к сервису, а сервис к репозиторию. Но есть и дополнительные действия, например, сохранение прикрепленного файла и запуск проверки работы.

Границу между контроллером и сервисом я бы оставила, т.к. контроллер должен отвечать за получение запроса и отправку ответа, а проверки и основные правила сдачи работы должны находиться в сервисе. Но внутри сервиса можно выделить отдельный класс с правилами можно ли сдавать, т.к. сейчас SubmissionService совмещает проверки, файлы и событие. При таком разделении удобно менять каждую часть программы, не затрагивая остальные.


# КАРТА ЗАВИСИМОСТЕЙ PETCLINIC — сценарий «добавление визита»

Источник      : spring-projects/spring-petclinic, ветка main,
                коммит 500158f732419217507c7656904b8e6aa1bcc0d6 (29.09.2026)
Среда         : DeepSeek Harness, sandbox workspace-write
Агент         : DSH single-agent (делегирование субагентам не использовалось)
Модель        : deepseek-flash
Дата анализа  : 2026-10-30

Все пути ниже — относительно
src/main/java/org/springframework/samples/petclinic/
(шаблоны — src/main/resources/templates/, схема — src/main/resources/db/).

Оговорка о версии: разобрана текущая main. В версии 2021 г. (коммит e7c879e)
схема была другой — отдельный VisitRepository.

сервисного слоя нет. В src/main/java нет ни одного класса
с @Service и ни одного файла *Service.java (единственный «сервис» —
тестовый пакет service/ClinicServiceTests.java, который на самом деле
тестирует репозитории).
6 @Controller (Visit, Owner, Pet, Vet, Welcome, Crash), web-хелперы (PetTypeFormatter, PetValidator, WebConfiguration, CacheConfiguration), 3 Spring Data-репозитория (OwnerRepository, PetTypeRepository, VetRepository), домен (Owner, Pet, Visit, Vet, PetType, Specialty), БД-скрипты. @Service — 0 совпадений; единственный «service» — тестовый ClinicServiceTests, тестирующий репозитории.
Цепочка:  VisitController.initNewVisitForm
    → VisitController.loadPetWithVisit
      → OwnerRepository.findById
        → SimpleJpaRepository.findById → EntityManager.find → Hibernate → БД
      → Owner.getPet(Integer) → (Pet)
      → new Visit() → Pet.addVisit(Visit)
    → шаблон createOrUpdateVisitForm.html

  VisitController.processNewVisitForm
    → (повторно loadPetWithVisit → OwnerRepository.findById → …)
    → Owner.addVisit(Integer, Visit) → Owner.getPet(Integer) → Pet.addVisit
    → OwnerRepository.save(Owner)
      → SimpleJpaRepository.save → EntityManager.merge
      → каскад Owner.pets → Pet.visits → Hibernate INSERT INTO visits
    → redirect:/owners/{ownerId}

Последовательность простая: контроллер сам оркестрирует загрузку агрегата,
изменение домена и сохранение; сервиса между контроллером и репозиторием нет.

Стрелки: По вызовам — вниз, обратных вызовов нет: OwnerRepository не знает о
VisitController, домен не знает о web. Но по зависимостям — нет, и вот
четыре места, где стрелка идёт не вниз:

  1) Прыжок через слой (web → persistence напрямую).
     Контроллер вызывает OwnerRepository и должен знать, что визит
     сохраняется как owners.save(owner), т.е. каскадом через агрегат Owner,
     а не через собственный репозиторий визита. Это знание устройства
     персистентности — в web-слое.

  2) Бизнес-правило в контроллере.
     «Дата визита должна быть в будущем» проверяется в
     processNewVisitForm (VisitController.java:100-102), а не в домене и
     не в сервисе. Правило и его сообщение об ошибке живут в web.

  3) Зависимость «вверх»: инфраструктура/фреймворк → домен.
     OwnerRepository extends JpaRepository<Owner,Integer>
     (OwnerRepository.java:36), а домен размечен @Entity, @NotBlank,
     @Size, @DateTimeFormat (Visit.java:35-45). Домен зависит от JPA и
     Bean Validation — «чистого» ядра нет: зависимость идёт из домена
     вверх, к инфраструктуре, а не наоборот.

  4) Стрелка «вбок/вверх» внутри агрегата.
     Owner.addVisit(petId, visit) (Owner.java:176) заставляет корень
     агрегата искать Pet и вызывать pet.addVisit; VisitController
     делает то же самое в loadPetWithVisit (VisitController.java:78-79),
     причём до валидации — web-фаза мутирует коллекцию pet.visits
     (на POST тот же объект добавляется повторно; для Set это
     идемпотентно). То есть web знает внутреннее строение
     Owner → Pet → Visit.

Дополнительно: PetValidator (web) валидирует домен, PetTypeFormatter (web)
ходит в PetTypeRepository — тоже «вбок», хотя формально вниз. А Visit
вообще не имеет репозитория: «слой визита» отсутствует, Visit — дочерняя
сущность Pet, и это ещё одна причина, по которой контроллер обязан знать
про агрегат.

Побочный эффект границы: Owner.pets и Pet.visits — EAGER (Owner.java:67,
Pet.java:56), поэтому добавление одного визита грузит владельца со всеми
питомцами и всеми их визитами; транзакция — только внутри save/findById
репозитория, а не на весь сценарий.

Граница иначе: VisitService.bookVisit(ownerId, petId, visit) с @Transactional — загрузка агрегата, инвариант, сохранение в одном месте; контроллер — только HTTP; пакеты разделить по слоям (web.owner vs owner), а не по предметной области.
Граница нужна, чтобы правило «визит добавляется только питомцу этого
владельца» и его транзакция жили в одном месте, а web-слой и способ
хранения можно было менять независимо.
