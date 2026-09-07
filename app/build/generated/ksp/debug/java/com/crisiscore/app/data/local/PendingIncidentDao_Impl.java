package com.crisiscore.app.data.local;

import android.database.Cursor;
import android.os.CancellationSignal;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.room.CoroutinesRoom;
import androidx.room.EntityInsertionAdapter;
import androidx.room.RoomDatabase;
import androidx.room.RoomSQLiteQuery;
import androidx.room.SharedSQLiteStatement;
import androidx.room.util.CursorUtil;
import androidx.room.util.DBUtil;
import androidx.sqlite.db.SupportSQLiteStatement;
import java.lang.Class;
import java.lang.Exception;
import java.lang.Object;
import java.lang.Override;
import java.lang.String;
import java.lang.SuppressWarnings;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Callable;
import javax.annotation.processing.Generated;
import kotlin.Unit;
import kotlin.coroutines.Continuation;

@Generated("androidx.room.RoomProcessor")
@SuppressWarnings({"unchecked", "deprecation"})
public final class PendingIncidentDao_Impl implements PendingIncidentDao {
  private final RoomDatabase __db;

  private final EntityInsertionAdapter<PendingIncidentEntity> __insertionAdapterOfPendingIncidentEntity;

  private final SharedSQLiteStatement __preparedStmtOfDeleteByIdempotencyKey;

  private final SharedSQLiteStatement __preparedStmtOfClearAll;

  private final SharedSQLiteStatement __preparedStmtOfIncrementRetryCount;

  public PendingIncidentDao_Impl(@NonNull final RoomDatabase __db) {
    this.__db = __db;
    this.__insertionAdapterOfPendingIncidentEntity = new EntityInsertionAdapter<PendingIncidentEntity>(__db) {
      @Override
      @NonNull
      protected String createQuery() {
        return "INSERT OR REPLACE INTO `pending_incidents` (`idempotencyKey`,`incidentJson`,`createdAt`,`retryCount`,`lastAttemptAt`) VALUES (?,?,?,?,?)";
      }

      @Override
      protected void bind(@NonNull final SupportSQLiteStatement statement,
          @NonNull final PendingIncidentEntity entity) {
        statement.bindString(1, entity.getIdempotencyKey());
        statement.bindString(2, entity.getIncidentJson());
        statement.bindLong(3, entity.getCreatedAt());
        statement.bindLong(4, entity.getRetryCount());
        statement.bindLong(5, entity.getLastAttemptAt());
      }
    };
    this.__preparedStmtOfDeleteByIdempotencyKey = new SharedSQLiteStatement(__db) {
      @Override
      @NonNull
      public String createQuery() {
        final String _query = "DELETE FROM pending_incidents WHERE idempotencyKey = ?";
        return _query;
      }
    };
    this.__preparedStmtOfClearAll = new SharedSQLiteStatement(__db) {
      @Override
      @NonNull
      public String createQuery() {
        final String _query = "DELETE FROM pending_incidents";
        return _query;
      }
    };
    this.__preparedStmtOfIncrementRetryCount = new SharedSQLiteStatement(__db) {
      @Override
      @NonNull
      public String createQuery() {
        final String _query = "UPDATE pending_incidents SET retryCount = retryCount + 1, lastAttemptAt = ? WHERE idempotencyKey = ?";
        return _query;
      }
    };
  }

  @Override
  public Object insert(final PendingIncidentEntity incident,
      final Continuation<? super Unit> $completion) {
    return CoroutinesRoom.execute(__db, true, new Callable<Unit>() {
      @Override
      @NonNull
      public Unit call() throws Exception {
        __db.beginTransaction();
        try {
          __insertionAdapterOfPendingIncidentEntity.insert(incident);
          __db.setTransactionSuccessful();
          return Unit.INSTANCE;
        } finally {
          __db.endTransaction();
        }
      }
    }, $completion);
  }

  @Override
  public Object deleteByIdempotencyKey(final String key,
      final Continuation<? super Unit> $completion) {
    return CoroutinesRoom.execute(__db, true, new Callable<Unit>() {
      @Override
      @NonNull
      public Unit call() throws Exception {
        final SupportSQLiteStatement _stmt = __preparedStmtOfDeleteByIdempotencyKey.acquire();
        int _argIndex = 1;
        _stmt.bindString(_argIndex, key);
        try {
          __db.beginTransaction();
          try {
            _stmt.executeUpdateDelete();
            __db.setTransactionSuccessful();
            return Unit.INSTANCE;
          } finally {
            __db.endTransaction();
          }
        } finally {
          __preparedStmtOfDeleteByIdempotencyKey.release(_stmt);
        }
      }
    }, $completion);
  }

  @Override
  public Object clearAll(final Continuation<? super Unit> $completion) {
    return CoroutinesRoom.execute(__db, true, new Callable<Unit>() {
      @Override
      @NonNull
      public Unit call() throws Exception {
        final SupportSQLiteStatement _stmt = __preparedStmtOfClearAll.acquire();
        try {
          __db.beginTransaction();
          try {
            _stmt.executeUpdateDelete();
            __db.setTransactionSuccessful();
            return Unit.INSTANCE;
          } finally {
            __db.endTransaction();
          }
        } finally {
          __preparedStmtOfClearAll.release(_stmt);
        }
      }
    }, $completion);
  }

  @Override
  public Object incrementRetryCount(final String key, final long now,
      final Continuation<? super Unit> $completion) {
    return CoroutinesRoom.execute(__db, true, new Callable<Unit>() {
      @Override
      @NonNull
      public Unit call() throws Exception {
        final SupportSQLiteStatement _stmt = __preparedStmtOfIncrementRetryCount.acquire();
        int _argIndex = 1;
        _stmt.bindLong(_argIndex, now);
        _argIndex = 2;
        _stmt.bindString(_argIndex, key);
        try {
          __db.beginTransaction();
          try {
            _stmt.executeUpdateDelete();
            __db.setTransactionSuccessful();
            return Unit.INSTANCE;
          } finally {
            __db.endTransaction();
          }
        } finally {
          __preparedStmtOfIncrementRetryCount.release(_stmt);
        }
      }
    }, $completion);
  }

  @Override
  public Object getAll(final Continuation<? super List<PendingIncidentEntity>> $completion) {
    final String _sql = "SELECT * FROM pending_incidents ORDER BY createdAt ASC";
    final RoomSQLiteQuery _statement = RoomSQLiteQuery.acquire(_sql, 0);
    final CancellationSignal _cancellationSignal = DBUtil.createCancellationSignal();
    return CoroutinesRoom.execute(__db, false, _cancellationSignal, new Callable<List<PendingIncidentEntity>>() {
      @Override
      @NonNull
      public List<PendingIncidentEntity> call() throws Exception {
        final Cursor _cursor = DBUtil.query(__db, _statement, false, null);
        try {
          final int _cursorIndexOfIdempotencyKey = CursorUtil.getColumnIndexOrThrow(_cursor, "idempotencyKey");
          final int _cursorIndexOfIncidentJson = CursorUtil.getColumnIndexOrThrow(_cursor, "incidentJson");
          final int _cursorIndexOfCreatedAt = CursorUtil.getColumnIndexOrThrow(_cursor, "createdAt");
          final int _cursorIndexOfRetryCount = CursorUtil.getColumnIndexOrThrow(_cursor, "retryCount");
          final int _cursorIndexOfLastAttemptAt = CursorUtil.getColumnIndexOrThrow(_cursor, "lastAttemptAt");
          final List<PendingIncidentEntity> _result = new ArrayList<PendingIncidentEntity>(_cursor.getCount());
          while (_cursor.moveToNext()) {
            final PendingIncidentEntity _item;
            final String _tmpIdempotencyKey;
            _tmpIdempotencyKey = _cursor.getString(_cursorIndexOfIdempotencyKey);
            final String _tmpIncidentJson;
            _tmpIncidentJson = _cursor.getString(_cursorIndexOfIncidentJson);
            final long _tmpCreatedAt;
            _tmpCreatedAt = _cursor.getLong(_cursorIndexOfCreatedAt);
            final int _tmpRetryCount;
            _tmpRetryCount = _cursor.getInt(_cursorIndexOfRetryCount);
            final long _tmpLastAttemptAt;
            _tmpLastAttemptAt = _cursor.getLong(_cursorIndexOfLastAttemptAt);
            _item = new PendingIncidentEntity(_tmpIdempotencyKey,_tmpIncidentJson,_tmpCreatedAt,_tmpRetryCount,_tmpLastAttemptAt);
            _result.add(_item);
          }
          return _result;
        } finally {
          _cursor.close();
          _statement.release();
        }
      }
    }, $completion);
  }

  @Override
  public Object getByIdempotencyKey(final String key,
      final Continuation<? super PendingIncidentEntity> $completion) {
    final String _sql = "SELECT * FROM pending_incidents WHERE idempotencyKey = ?";
    final RoomSQLiteQuery _statement = RoomSQLiteQuery.acquire(_sql, 1);
    int _argIndex = 1;
    _statement.bindString(_argIndex, key);
    final CancellationSignal _cancellationSignal = DBUtil.createCancellationSignal();
    return CoroutinesRoom.execute(__db, false, _cancellationSignal, new Callable<PendingIncidentEntity>() {
      @Override
      @Nullable
      public PendingIncidentEntity call() throws Exception {
        final Cursor _cursor = DBUtil.query(__db, _statement, false, null);
        try {
          final int _cursorIndexOfIdempotencyKey = CursorUtil.getColumnIndexOrThrow(_cursor, "idempotencyKey");
          final int _cursorIndexOfIncidentJson = CursorUtil.getColumnIndexOrThrow(_cursor, "incidentJson");
          final int _cursorIndexOfCreatedAt = CursorUtil.getColumnIndexOrThrow(_cursor, "createdAt");
          final int _cursorIndexOfRetryCount = CursorUtil.getColumnIndexOrThrow(_cursor, "retryCount");
          final int _cursorIndexOfLastAttemptAt = CursorUtil.getColumnIndexOrThrow(_cursor, "lastAttemptAt");
          final PendingIncidentEntity _result;
          if (_cursor.moveToFirst()) {
            final String _tmpIdempotencyKey;
            _tmpIdempotencyKey = _cursor.getString(_cursorIndexOfIdempotencyKey);
            final String _tmpIncidentJson;
            _tmpIncidentJson = _cursor.getString(_cursorIndexOfIncidentJson);
            final long _tmpCreatedAt;
            _tmpCreatedAt = _cursor.getLong(_cursorIndexOfCreatedAt);
            final int _tmpRetryCount;
            _tmpRetryCount = _cursor.getInt(_cursorIndexOfRetryCount);
            final long _tmpLastAttemptAt;
            _tmpLastAttemptAt = _cursor.getLong(_cursorIndexOfLastAttemptAt);
            _result = new PendingIncidentEntity(_tmpIdempotencyKey,_tmpIncidentJson,_tmpCreatedAt,_tmpRetryCount,_tmpLastAttemptAt);
          } else {
            _result = null;
          }
          return _result;
        } finally {
          _cursor.close();
          _statement.release();
        }
      }
    }, $completion);
  }

  @NonNull
  public static List<Class<?>> getRequiredConverters() {
    return Collections.emptyList();
  }
}
