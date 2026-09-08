package com.crisiscore.app.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.crisiscore.app.CrisisCoreApp
import com.crisiscore.app.data.model.FamilyMember
import com.crisiscore.app.data.model.FamilyMemberStatus
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class FamilyViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = (application as? CrisisCoreApp)?.repository
        ?: com.crisiscore.app.data.repository.CrisisCoreRepository(application)

    val familyList: StateFlow<List<FamilyMember>> = repository.getFamilyMembersFlow()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    init {
        // Seed self user if family list is empty
        viewModelScope.launch {
            val current = repository.getAllFamilyMembers()
            if (current.isEmpty()) {
                val selfMember = FamilyMember(
                    id = "self-user",
                    name = "You",
                    relationship = "Self",
                    status = FamilyMemberStatus.NEEDS_CHECKIN,
                    location = "Current Location",
                    isSelf = true
                )
                repository.addFamilyMember(selfMember)
            }
        }
    }

    fun addMember(name: String, relationship: String) {
        viewModelScope.launch {
            val newMember = FamilyMember(
                id = "mem-${System.currentTimeMillis()}",
                name = name,
                relationship = relationship,
                status = FamilyMemberStatus.NEEDS_CHECKIN,
                location = "Awaiting Check-in"
            )
            repository.addFamilyMember(newMember)
        }
    }

    fun markSelfSafe() {
        viewModelScope.launch {
            val self = familyList.value.firstOrNull { it.isSelf }
            if (self != null) {
                repository.updateFamilyMemberStatus(
                    id = self.id,
                    status = FamilyMemberStatus.CHECKED_IN,
                    checkedInBy = "Self",
                    checkedInAt = "Just now"
                )
            }
        }
    }

    fun checkInMembers(ids: List<String>) {
        viewModelScope.launch {
            ids.forEach { id ->
                repository.updateFamilyMemberStatus(
                    id = id,
                    status = FamilyMemberStatus.CHECKED_IN,
                    checkedInBy = "Checked in",
                    checkedInAt = "Just now"
                )
            }
        }
    }

    fun deleteMember(id: String) {
        viewModelScope.launch {
            repository.deleteFamilyMember(id)
        }
    }
}
