package com.crisiscore.app.data.local

import androidx.room.*
import com.crisiscore.app.data.model.IncidentRequest
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

@Entity(tableName = "pending_incidents")
data class PendingIncidentEntity(
    @PrimaryKey val idempotencyKey: String,
    val incidentJson: String,
    val createdAt: Long = System.currentTimeMillis(),
    val retryCount: Int = 0,
    val lastAttemptAt: Long = 0
) {
    fun toIncidentRequest(json: Json = Json.Default): IncidentRequest =
        json.decodeFromString(incidentJson)
}

@Dao
interface PendingIncidentDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(incident: PendingIncidentEntity)

    @Query("SELECT * FROM pending_incidents ORDER BY createdAt ASC")
    suspend fun getAll(): List<PendingIncidentEntity>

    @Query("SELECT * FROM pending_incidents WHERE idempotencyKey = :key")
    suspend fun getByIdempotencyKey(key: String): PendingIncidentEntity?

    @Query("DELETE FROM pending_incidents WHERE idempotencyKey = :key")
    suspend fun deleteByIdempotencyKey(key: String)

    @Query("DELETE FROM pending_incidents")
    suspend fun clearAll()

    @Query("UPDATE pending_incidents SET retryCount = retryCount + 1, lastAttemptAt = :now WHERE idempotencyKey = :key")
    suspend fun incrementRetryCount(key: String, now: Long)
}

@Database(entities = [PendingIncidentEntity::class], version = 1, exportSchema = false)
abstract class OfflineDatabase : RoomDatabase() {
    abstract fun pendingIncidentDao(): PendingIncidentDao

    companion object {
        @Volatile private var INSTANCE: OfflineDatabase? = null

        fun getInstance(context: android.content.Context): OfflineDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    OfflineDatabase::class.java,
                    "offline_database"
                ).build().also { INSTANCE = it }
            }
    }
}