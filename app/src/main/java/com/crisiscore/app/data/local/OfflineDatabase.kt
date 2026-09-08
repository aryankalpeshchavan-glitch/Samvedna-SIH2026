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

    @Query("DELETE FROM pending_incidents WHERE retryCount >= :maxRetries")
    suspend fun deleteExceededRetries(maxRetries: Int = 5)
}

@Entity(tableName = "family_members")
data class FamilyMemberEntity(
    @PrimaryKey val id: String,
    val name: String,
    val relationship: String,
    val status: String,
    val checkedInBy: String? = null,
    val checkedInAt: String? = null,
    val location: String? = null,
    val isSelf: Boolean = false
) {
    fun toFamilyMember(): com.crisiscore.app.data.model.FamilyMember = com.crisiscore.app.data.model.FamilyMember(
        id = id,
        name = name,
        relationship = relationship,
        status = try {
            com.crisiscore.app.data.model.FamilyMemberStatus.valueOf(status)
        } catch (e: Exception) {
            com.crisiscore.app.data.model.FamilyMemberStatus.NEEDS_CHECKIN
        },
        checkedInBy = checkedInBy,
        checkedInAt = checkedInAt,
        location = location,
        isSelf = isSelf
    )

    companion object {
        fun fromFamilyMember(member: com.crisiscore.app.data.model.FamilyMember): FamilyMemberEntity = FamilyMemberEntity(
            id = member.id,
            name = member.name,
            relationship = member.relationship,
            status = member.status.name,
            checkedInBy = member.checkedInBy,
            checkedInAt = member.checkedInAt,
            location = member.location,
            isSelf = member.isSelf
        )
    }
}

@Dao
interface FamilyMemberDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(member: FamilyMemberEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(members: List<FamilyMemberEntity>)

    @Query("SELECT * FROM family_members ORDER BY isSelf DESC, name ASC")
    fun getAllFlow(): kotlinx.coroutines.flow.Flow<List<FamilyMemberEntity>>

    @Query("SELECT * FROM family_members ORDER BY isSelf DESC, name ASC")
    suspend fun getAll(): List<FamilyMemberEntity>

    @Query("UPDATE family_members SET status = :status, checkedInBy = :checkedInBy, checkedInAt = :checkedInAt WHERE id = :id")
    suspend fun updateStatus(id: String, status: String, checkedInBy: String?, checkedInAt: String?)

    @Query("DELETE FROM family_members WHERE id = :id")
    suspend fun deleteById(id: String)
}

@Database(entities = [PendingIncidentEntity::class, FamilyMemberEntity::class], version = 2, exportSchema = false)
abstract class OfflineDatabase : RoomDatabase() {
    abstract fun pendingIncidentDao(): PendingIncidentDao
    abstract fun familyMemberDao(): FamilyMemberDao

    companion object {
        @Volatile private var INSTANCE: OfflineDatabase? = null

        fun getInstance(context: android.content.Context): OfflineDatabase =
            INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    OfflineDatabase::class.java,
                    "offline_database"
                )
                .fallbackToDestructiveMigration()
                .build().also { INSTANCE = it }
            }
    }
}