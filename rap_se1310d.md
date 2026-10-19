# Rapport SE1310D — ouverture de crédit

## Objectif et périmètre

Ajout de la route `POST /api/credits/redeem` avec coupon à usage contrôlé, HMAC-SHA256, vérification CSRF, limitation de cinq tentatives par minute et journalisation des tentatives. Ajout d’une modale « Ajouter du crédit » à côté de la jauge : le formulaire coupon affiche le résultat et la section de recharge reste désactivée avec la mention « bientôt ». Aucun code de paiement, aucune migration et aucun changement du flux de métrage.

## Fichiers modifiés

- `app.py` : route de redemption, validation/transaction du crédit, CSRF par cookie/formulaire selon le schéma existant, limiteur par utilisateur et messages de résultat sans divulguer la raison d’un refus.
- `templates/coach.html` : bouton près de la jauge et modale coupon/recharge désactivée.
- `static/app.js` : soumission du formulaire coupon à la route et affichage du résultat dans la modale.
- `tests/test_coupons.py` : garde sur le nom de la base issu du `.env`, scénarios demandés dans des transactions rollbackées, secret HMAC exclusivement défini dans le fichier de test et scénario de concurrence ignoré.

## Environnement observé

- OBSERVÉ : le garde du test accepte la base nommée `coach_proto` dans le `.env` du projet. Aucune valeur de connexion n’est reproduite ici.
- OBSERVÉ : l’ouverture de connexion PostgreSQL échoue avec `Operation not permitted` sur le socket local. Les scénarios nécessitant la base s’arrêtent dans `setUp`, avant toute écriture de fixture.
- NON OBSERVÉ : état de santé du service et comportement dans un navigateur; aucun appel au service et aucun test navigateur n’ont été effectués.

## Sortie complète de unittest

Commande : `/home/nicee/coach/.venv/bin/python -m unittest tests/test_coupons.py -v`

```text
test_concurrent_redemption (tests.test_coupons.CouponTests.test_concurrent_redemption) ... skipped 'nécessite une base de test dédiée'
test_duplicate_user_redemption_refused_without_balance_change (tests.test_coupons.CouponTests.test_duplicate_user_redemption_refused_without_balance_change) ... ERROR
test_expired_inactive_unknown_same_generic_message (tests.test_coupons.CouponTests.test_expired_inactive_unknown_same_generic_message) ... ERROR
test_plain_code_is_not_stored_in_any_coupon_or_ledger_table (tests.test_coupons.CouponTests.test_plain_code_is_not_stored_in_any_coupon_or_ledger_table) ... ERROR
test_redemption_limit_blocks_second_user (tests.test_coupons.CouponTests.test_redemption_limit_blocks_second_user) ... ERROR
test_valid_coupon_credits_exact_amount_and_ledger (tests.test_coupons.CouponTests.test_valid_coupon_credits_exact_amount_and_ledger) ... ERROR

======================================================================
ERROR: test_duplicate_user_redemption_refused_without_balance_change (tests.test_coupons.CouponTests.test_duplicate_user_redemption_refused_without_balance_change)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
psycopg2.OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/nicee/coach/tests/test_coupons.py", line 29, in setUp
    self.connection = coach.engine.connect()
                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3260, in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 151, in __init__
    Connection._handle_dbapi_exception_noconnection(
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2417, in _handle_dbapi_exception_noconnection
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?

(Background on this error at: https://sqlalche.me/e/21/e3q8)

======================================================================
ERROR: test_expired_inactive_unknown_same_generic_message (tests.test_coupons.CouponTests.test_expired_inactive_unknown_same_generic_message)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
psycopg2.OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/nicee/coach/tests/test_coupons.py", line 29, in setUp
    self.connection = coach.engine.connect()
                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3260, in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 151, in __init__
    Connection._handle_dbapi_exception_noconnection(
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2417, in _handle_dbapi_exception_noconnection
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?

(Background on this error at: https://sqlalche.me/e/21/e3q8)

======================================================================
ERROR: test_plain_code_is_not_stored_in_any_coupon_or_ledger_table (tests.test_coupons.CouponTests.test_plain_code_is_not_stored_in_any_coupon_or_ledger_table)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
psycopg2.OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/nicee/coach/tests/test_coupons.py", line 29, in setUp
    self.connection = coach.engine.connect()
                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3260, in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 151, in __init__
    Connection._handle_dbapi_exception_noconnection(
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2417, in _handle_dbapi_exception_noconnection
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?

(Background on this error at: https://sqlalche.me/e/21/e3q8)

======================================================================
ERROR: test_redemption_limit_blocks_second_user (tests.test_coupons.CouponTests.test_redemption_limit_blocks_second_user)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
psycopg2.OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/nicee/coach/tests/test_coupons.py", line 29, in setUp
    self.connection = coach.engine.connect()
                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3260, in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 151, in __init__
    Connection._handle_dbapi_exception_noconnection(
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2417, in _handle_dbapi_exception_noconnection
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?

(Background on this error at: https://sqlalche.me/e/21/e3q8)

======================================================================
ERROR: test_valid_coupon_credits_exact_amount_and_ledger (tests.test_coupons.CouponTests.test_valid_coupon_credits_exact_amount_and_ledger)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
psycopg2.OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/nicee/coach/tests/test_coupons.py", line 29, in setUp
    self.connection = coach.engine.connect()
                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3260, in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 151, in __init__
    Connection._handle_dbapi_exception_noconnection(
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 2417, in _handle_dbapi_exception_noconnection
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 149, in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/base.py", line 3284, in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 445, in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 1303, in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 709, in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 176, in _do_get
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/impl.py", line 174, in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 386, in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 671, in __init__
    self.__connect()
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 906, in __connect
    with util.safe_reraise():
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py", line 166, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/pool/base.py", line 902, in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/create.py", line 645, in connect
    return dialect.connect(*cargs_tup, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/sqlalchemy/engine/default.py", line 869, in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nicee/coach/.venv/lib/python3.12/site-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?

(Background on this error at: https://sqlalche.me/e/21/e3q8)

----------------------------------------------------------------------
Ran 6 tests in 0.007s

FAILED (errors=5, skipped=1)

```

## Non testé

- Test de concurrence : reporté, marqué skip avec la raison « nécessite une base de test dédiée ».
- Paiement : hors périmètre; aucune intégration réalisée.
- Test navigateur : non effectué.
- Les scénarios de coupons sont écrits mais ne sont pas validés en exécution tant que la connexion PostgreSQL reste inaccessible dans cet environnement.

## Actions réservées au propriétaire

1. Redémarrer `coach-prototype.service`.
2. Vérifier `/health`.
3. Créer un coupon avec `m_coupon.py`.
4. Tester la redemption sur le compte 2.

Aucun service n’a été redémarré, aucune migration appliquée et aucune écriture dans `fu19_db` effectuée.


## SE1310D-bis — actualisation immédiate de la jauge

### Diff résumé

- `static/app.js` : après une réponse coupon réussie seulement, lecture et validation entière de `credit_micro_usd`, calcul du libellé en dollars/centimes avec des entiers, puis mise à jour de `#credit-label`, `aria-valuenow`, `aria-valuemax` et de la largeur de la barre. Aucun nouveau appel réseau et aucun rechargement de page.
- `templates/coach.html` : aucun changement nécessaire, les identifiants requis existaient déjà.

### Tests manuels à effectuer par le propriétaire

1. Avec un coupon valide, vérifier que la jauge et son libellé changent immédiatement sans rechargement.
2. Avec un coupon refusé, vérifier que la jauge et son libellé ne changent pas et que le message d’erreur générique reste visible dans la modale.
3. Recharger ensuite la page et vérifier que la valeur affichée par le serveur est identique à celle observée après l’ajout.

- NON OBSERVÉ : tests manuels et rendu navigateur, non exécutés par Codex comme demandé.
- OBSERVÉ : seul `static/app.js` a été modifié pour cette sous-mission; aucun service redémarré et aucun déploiement effectué.
