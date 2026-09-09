package com.crisiscore.app.data.local

import android.content.Context
import androidx.room.*
import com.crisiscore.app.data.model.IncidentReportPayload
import com.crisiscore.app.data.model.SosPayload
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "pending_sos")
data class PendingSosEntity(
    @PrimaryKey val id: String,
    val payloadJson: String,
    val createdAt: Long,
    val synced: Boolean = false,
    val attempts: Int = 0
)

@Entity(tableName = "pending_incidents")
data class PendingIncidentEntity(
    @PrimaryKey val id: String,
    val payloadJson: String,
    val createdAt: Long,
    val synced: Boolean = false,
    val attempts: Int = 0
)

@Dao
interface OfflineDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSos(entry: PendingSosEntity)

    @Query("SELECT * FROM pending_sos ORDER BY createdAt DESC")
    fun getAllSos(): Flow<List<PendingSosEntity>>

    @Query("SELECT * FROM pending_sos WHERE synced = 0")
    suspend fun getUnsyncedSos(): List<PendingSosEntity>

    @Query("UPDATE pending_sos SET synced = 1 WHERE id = :id")
    suspend fun markSosSynced(id: String)

    @Delete
    suspend fun deleteSos(entry: PendingSosEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertIncident(entry: PendingIncidentEntity)

    @Query("SELECT * FROM pending_incidents ORDER BY createdAt DESC")
    fun getAllIncidents(): Flow<List<PendingIncidentEntity>>

    @Query("SELECT * FROM pending_incidents WHERE synced = 0")
    suspend fun getUnsyncedIncidents(): List<PendingIncidentEntity>

    @Query("UPDATE pending_incidents SET synced = 1 WHERE id = :id")
    suspend fun markIncidentSynced(id: String)

    @Delete
    suspend fun deleteIncident(entry: PendingIncidentEntity)
}

@Database(entities = [PendingSosEntity::class, PendingIncidentEntity::class], version = 1, exportSchema = false)
abstract class CrisisCoreDatabase : RoomDatabase() {
    abstract fun offlineDao(): OfflineDao

    companion object {
        @Volatile
        private var INSTANCE: CrisisCoreDatabase? = null

        fun getInstance(context: Context): CrisisCoreDatabase {
            return INSTANCE ?: synchronized(this) {
                Room.databaseBuilder(
                    context.applicationContext,
                    CrisisCoreDatabase::class.java,
                    "crisiscore_offline.db"
                ).build().also { INSTANCE = it }
            }
        }
    }
}
