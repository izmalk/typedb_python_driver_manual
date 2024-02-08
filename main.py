from typedb.driver import TypeDB, SessionType, TransactionType, TypeDBOptions

DB_NAME = "sample_db2"
SERVER_ADDR = "127.0.0.1:1729"

print("TypeDB Manual sample code")

with TypeDB.core_driver("localhost:1729") as driver:
    for db in driver.databases.all():
        print(db.name)
    if driver.databases.contains(DB_NAME):
        driver.databases.get(DB_NAME).delete()
    driver.databases.create(DB_NAME)

    assert driver.databases.contains(DB_NAME), "Database creation error."
    print("Database setup complete.")

    with driver.session(DB_NAME, SessionType.SCHEMA) as session:
        with session.transaction(TransactionType.WRITE) as transaction:
            define_query = """
                            define
                            email sub attribute, value string;
                            name sub attribute, value string;
                            friendship sub relation, relates friend;
                            user sub entity,
                                owns email @key,
                                owns name,
                                plays friendship:friend;
                            admin sub user;
                            """
            transaction.query.define(define_query)
            transaction.commit()

    with driver.session(DB_NAME, SessionType.SCHEMA) as session:
        with session.transaction(TransactionType.WRITE) as transaction:
            undefine_query = "undefine admin sub user;"
            transaction.query.undefine(undefine_query)
            transaction.commit()

    with driver.session(DB_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.WRITE) as transaction:
            insert_query = """
                            insert
                            $user1 isa user, has name "Alice", has email "alice@vaticle.com";
                            $user2 isa user, has name "Bob", has email "bob@vaticle.com";
                            $friendship (friend:$user1, friend: $user2) isa friendship;
                            """
            transaction.query.insert(insert_query)
            transaction.commit()

    with driver.session(DB_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.WRITE) as transaction:
            match_insert_query = """
                                    match
                                    $u isa user, has name "Bob";
                                    insert
                                    $new-u isa user, has name "Charlie", has email "charlie@vaticle.com";
                                    $f($u,$new-u) isa friendship;
                                    """
            response = list(transaction.query.insert(match_insert_query))
            if len(response) == 1:
                transaction.commit()
            else:
                transaction.close()

    with driver.session(DB_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.WRITE) as transaction:
            delete_query = """
                            match
                            $u isa user, has name "Charlie";
                            $f ($u) isa friendship;
                            delete
                            $f isa friendship;
                            """
            transaction.query.delete(delete_query)
            transaction.commit()

    with driver.session(DB_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.WRITE) as transaction:
            update_query = """
                            match
                            $u isa user, has name "Charlie", has email $e;
                            delete
                            $u has $e;
                            insert
                            $u has email "charles@vaticle.com";
                            """
            response = list(transaction.query.update(update_query))
            if len(response) == 1:
                transaction.commit()
            else:
                transaction.close()

    with driver.session(DB_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.READ) as transaction:
            fetch_query = """
                            match
                            $u isa user;
                            fetch
                            $u: name, email;
                            """
            response = transaction.query.fetch(fetch_query)
            for i, JSON in enumerate(response):
                print(f"User #{i + 1}: {JSON}")

    with driver.session(DB_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.READ) as transaction:
            get_query = """
                        match
                        $u isa user, has email $e;
                        get
                        $e;
                        """
            response = transaction.query.get(get_query)
            for i, concept_map in enumerate(response):
                email = concept_map.get("e").as_attribute().get_value()
                print(f"Email #{i + 1}: {email}")

# --------------------- Inference ---------------------

    with driver.session(DB_NAME, SessionType.SCHEMA) as session:
        with session.transaction(TransactionType.WRITE) as transaction:
            define_query = """
                            define
                            rule users:
                            when {
                                $u isa user;
                            } then {
                                $u has name "User";
                            };
                            """
            transaction.query.define(define_query)
            transaction.commit()

    with driver.session(DB_NAME, SessionType.DATA) as session:
        with session.transaction(TransactionType.READ, TypeDBOptions(infer=True)) as transaction:
            fetch_query = """
                            match
                            $u isa user;
                            fetch
                            $u: name, email;
                            """
            response = transaction.query.fetch(fetch_query)
            for i, JSON in enumerate(response):
                print(f"User #{i + 1}: {JSON}")
