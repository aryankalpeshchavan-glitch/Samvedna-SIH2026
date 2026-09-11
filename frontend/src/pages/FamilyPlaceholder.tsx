import React, { useRef, useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { DataSourceBadge } from '../components/ui/DataSourceBadge';
import { ModalPortal } from '../components/ui/ModalPortal';

import { animatePageEnter } from '../animations/pageTransitions';
import { useTranslation } from '../i18n/LanguageContext';
import { Users, ShieldCheck, UserPlus, CheckCircle2, UserCheck, PhoneCall, X, Heart, HeartHandshake, MapPin, HandHeart } from 'lucide-react';

import { useToast } from '../context/ToastContext';

export interface FamilyMemberItem {
  id: string;
  name: string;
  relationship: string;
  status: 'CHECKED_IN' | 'NEEDS_CHECKIN' | 'UNVERIFIED';
  checkedInBy?: string;
  checkedInAt?: string;
  location?: string;
  isSelf?: boolean;
}

export interface CommunitySafetyReport {
  id: string;
  name?: string;
  context: string;
  location: string;
  timestamp: string;
}

export const FamilyPlaceholder: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation();
  const { success } = useToast();

  // Initial Mock Family Members State
  const [familyList, setFamilyList] = useState<FamilyMemberItem[]>([
    {
      id: 'mem-self',
      name: 'Priya Sharma (You)',
      relationship: 'Self',
      status: 'CHECKED_IN',
      checkedInBy: 'Self',
      checkedInAt: '5 min ago',
      location: 'Guwahati Sector 4',
      isSelf: true,
    },
    {
      id: 'mem-1',
      name: 'Rahul Sharma',
      relationship: 'Son',
      status: 'CHECKED_IN',
      checkedInBy: 'Checked in by Priya (You)',
      checkedInAt: '5 min ago',
      location: 'Community Shelter B',
      isSelf: false,
    },
    {
      id: 'mem-2',
      name: 'Ananya Sharma',
      relationship: 'Daughter',
      status: 'NEEDS_CHECKIN',
      location: 'School High Ground Shelter',
      isSelf: false,
    },
    {
      id: 'mem-3',
      name: 'Rajesh Sharma',
      relationship: 'Brother',
      status: 'UNVERIFIED',
      location: 'Dispur Hill Sector 2',
      isSelf: false,
    },
  ]);

  // Community Reports State
  const [communityReports, setCommunityReports] = useState<CommunitySafetyReport[]>([
    {
      id: 'comm-1',
      name: 'Ramen Das',
      context: 'Elderly neighbor',
      location: 'High School Ground Shelter',
      timestamp: '12 min ago',
    },
    {
      id: 'comm-2',
      name: 'Bina Roy',
      context: 'Local Shopkeeper',
      location: 'Sector 4 Community Hall',
      timestamp: '25 min ago',
    },
  ]);

  // Modal States
  const [isCheckInOthersOpen, setIsCheckInOthersOpen] = useState(false);
  const [isAddMemberOpen, setIsAddMemberOpen] = useState(false);
  const [isReportSomeoneOpen, setIsReportSomeoneOpen] = useState(false);
  const [selectedForCheckIn, setSelectedForCheckIn] = useState<string[]>([]);

  // Form States for Add Member
  const [newMemberName, setNewMemberName] = useState('');
  const [newMemberRel, setNewMemberRel] = useState('Relative');

  // Form States for "Report Someone As Safe"
  const [reportPersonName, setReportPersonName] = useState('');
  const [reportContext, setReportContext] = useState('Someone I Encountered');
  const [reportLocation, setReportLocation] = useState('Guwahati Sector 4 (Current GPS)');
  const [isConfirmedSafe, setIsConfirmedSafe] = useState(false);

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  // Summary Counts
  const totalPeople = familyList.length;
  const checkedInCount = familyList.filter((m) => m.status === 'CHECKED_IN').length;
  const percentAccounted = Math.round((checkedInCount / totalPeople) * 100);

  // Trigger Toast Notification
  const showToast = (msg: string) => {
    success(msg);
  };

  // 1. Self Check-In Action ("I'M SAFE")
  const handleSelfCheckIn = () => {
    setFamilyList((prev) =>
      prev.map((m) =>
        m.isSelf
          ? {
              ...m,
              status: 'CHECKED_IN',
              checkedInBy: 'Self',
              checkedInAt: 'Just now',
            }
          : m
      )
    );
    showToast('You have been marked SAFE!');
  };

  // 2. Proxy Check-In Action ("CHECK IN SOMEONE WITH ME")
  const handleConfirmCheckInOthers = () => {
    if (selectedForCheckIn.length === 0) return;

    setFamilyList((prev) =>
      prev.map((m) =>
        selectedForCheckIn.includes(m.id)
          ? {
              ...m,
              status: 'CHECKED_IN',
              checkedInBy: 'Checked in by Priya (You)',
              checkedInAt: 'Just now',
            }
          : m
      )
    );

    showToast(`Checked in ${selectedForCheckIn.length} family member(s) with you!`);
    setSelectedForCheckIn([]);
    setIsCheckInOthersOpen(false);
  };

  // 3. Add Family Member
  const handleAddMemberSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemberName.trim()) return;

    const newMember: FamilyMemberItem = {
      id: `mem-${Date.now()}`,
      name: newMemberName.trim(),
      relationship: newMemberRel,
      status: 'NEEDS_CHECKIN',
      location: 'Awaiting Check-in',
      isSelf: false,
    };

    setFamilyList((prev) => [...prev, newMember]);
    showToast(`Added ${newMemberName} to family list.`);
    setNewMemberName('');
    setNewMemberRel('Relative');
    setIsAddMemberOpen(false);
  };

  // 4. Report Someone As Safe (Community Safety Action)
  const handleReportSomeoneSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isConfirmedSafe) return;

    const newReport: CommunitySafetyReport = {
      id: `comm-${Date.now()}`,
      name: reportPersonName.trim() || 'Unidentified Person',
      context: reportContext,
      location: reportLocation.trim() || 'Current GPS Location',
      timestamp: 'Just now',
    };

    setCommunityReports((prev) => [newReport, ...prev]);
    showToast(t('family.reportSuccessTitle'));
    setReportPersonName('');
    setIsConfirmedSafe(false);
    setIsReportSomeoneOpen(false);
  };

  // 5. Request Check-in SMS
  const handleRequestCheckIn = (memberName: string) => {
    showToast(`SMS Check-In request sent to ${memberName}!`);
  };

  return (
    <div ref={containerRef} className="pb-28 pt-4 px-4 max-w-2xl mx-auto space-y-6 font-sans">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#C7B89B]/50">
        <div>
          <span className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-widest block">
            COMMUNITY MESH & FAMILY NETWORK
          </span>
          <h2 className="text-xl font-heading font-black text-[#202622] uppercase tracking-wide px-2 py-0.5">
            {t('family.title')}
          </h2>
        </div>
        <DataSourceBadge type="synthetic" />
      </div>

      {/* 1. FAMILY SAFETY SUMMARY BAR */}
      <Card className="p-5 border-2 border-[#23483A]/30 bg-[#FAF9F3] space-y-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2.5 rounded-2xl bg-[#23483A]/10 text-[#23483A]">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] font-mono font-bold text-[#23483A] uppercase tracking-widest block">
                FAMILY STATUS SUMMARY
              </span>
              <h3 className="text-base font-heading font-black text-[#202622]">
                {t('family.summary', { count: checkedInCount, total: totalPeople })}
              </h3>
            </div>
          </div>
          <span className="px-3 py-1 rounded-xl bg-[#23483A]/10 text-[#23483A] font-mono font-bold text-xs">
            {percentAccounted}% Safe
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2.5 rounded-full bg-[#E8E6DC] overflow-hidden border border-[#C7B89B]/40">
          <div
            className="h-full bg-[#23483A] transition-all duration-500"
            style={{ width: `${percentAccounted}%` }}
          />
        </div>
      </Card>

      {/* 2. PROMINENT FAMILY ACTIONS (I'M SAFE vs CHECK IN SOMEONE WITH ME) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Action 1: Self Check-In ("I'M SAFE") */}
        <button
          onClick={handleSelfCheckIn}
          className="p-4 rounded-2xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-sm hover:bg-[#1b382d] transition-all flex items-center justify-center space-x-2.5 shadow-md cursor-pointer tactile-press"
        >
          <CheckCircle2 className="w-5 h-5 text-[#FAF9F3]" />
          <span>{t('family.imSafe')}</span>
        </button>

        {/* Action 2: Proxy Check-In ("CHECK IN SOMEONE WITH ME") */}
        <button
          onClick={() => setIsCheckInOthersOpen(true)}
          className="p-4 rounded-2xl bg-[#FAF9F3] border-2 border-[#23483A] text-[#23483A] font-heading font-bold text-sm hover:bg-[#23483A]/10 transition-all flex items-center justify-center space-x-2.5 shadow-sm cursor-pointer tactile-press"
        >
          <UserCheck className="w-5 h-5 text-[#23483A]" />
          <span>{t('family.checkInOthers')}</span>
        </button>
      </div>

      {/* 3. FAMILY MEMBER CARDS */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-bold text-[#536A72] uppercase tracking-widest">
            FAMILY MEMBERS ({familyList.length})
          </span>
          <button
            onClick={() => setIsAddMemberOpen(true)}
            className="text-xs font-heading font-bold text-[#23483A] hover:underline flex items-center space-x-1 cursor-pointer"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>{t('family.addMemberBtn')}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 gap-3">
          {familyList.map((member) => {
            const isChecked = member.status === 'CHECKED_IN';
            const isNeeds = member.status === 'NEEDS_CHECKIN';

            return (
              <Card key={member.id} className="p-4 bg-[#FAF9F3] border-[#C7B89B] shadow-sm space-y-2.5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  
                  {/* Member Name & Relationship Badge */}
                  <div className="flex items-start space-x-3">
                    <div className={`p-2.5 rounded-2xl shrink-0 ${
                      isChecked ? 'bg-[#23483A]/10 text-[#23483A]' : isNeeds ? 'bg-[#D88A32]/15 text-[#D88A32]' : 'bg-[#8E2F2B]/10 text-[#8E2F2B]'
                    }`}>
                      {member.relationship === 'Son' || member.relationship === 'Daughter' ? (
                        <Heart className="w-5 h-5" />
                      ) : member.isSelf ? (
                        <ShieldCheck className="w-5 h-5" />
                      ) : (
                        <Users className="w-5 h-5" />
                      )}
                    </div>

                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="text-base font-heading font-bold text-[#202622]">
                          {member.name}
                        </h4>
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#202622]/10 text-[#536A72]">
                          {member.relationship}
                        </span>
                      </div>

                      {/* Status Line */}
                      <div className="mt-1 flex items-center space-x-1.5 text-xs font-mono">
                        {isChecked ? (
                          <span className="text-[#23483A] font-bold flex items-center">
                            <span className="w-2 h-2 rounded-full bg-[#23483A] inline-block mr-1.5" />
                            {member.checkedInBy ? member.checkedInBy : t('family.checkedIn')} &bull; {member.checkedInAt || 'Just now'}
                          </span>
                        ) : isNeeds ? (
                          <span className="text-[#D88A32] font-bold flex items-center">
                            <span className="w-2 h-2 rounded-full bg-[#D88A32] inline-block mr-1.5" />
                            {t('family.notCheckedIn')}
                          </span>
                        ) : (
                          <span className="text-[#8E2F2B] font-bold flex items-center">
                            <span className="w-2 h-2 rounded-full bg-[#8E2F2B] inline-block mr-1.5 animate-ping" />
                            {t('family.needsCheckIn')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions / Location */}
                  <div className="flex items-center justify-between sm:justify-end space-x-2 pt-2 sm:pt-0 border-t sm:border-t-0 border-[#E8E6DC]">
                    {member.location && (
                      <span className="text-[11px] font-mono text-[#536A72]">
                        📍 {member.location}
                      </span>
                    )}

                    {!isChecked && (
                      <button
                        onClick={() => handleRequestCheckIn(member.name)}
                        className="px-3 py-1.5 rounded-xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/30 text-[#8E2F2B] font-heading font-bold text-xs hover:bg-[#8E2F2B] hover:text-[#FAF9F3] transition-colors flex items-center space-x-1 cursor-pointer shrink-0"
                      >
                        <PhoneCall className="w-3.5 h-3.5" />
                        <span>{t('family.requestCheckIn')}</span>
                      </button>
                    )}
                  </div>

                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* 4. VISUALLY SEPARATED "HELP SOMEONE ELSE" / COMMUNITY SAFETY AREA */}
      <div className="mt-8 pt-6 border-t-2 border-dashed border-[#C7B89B]/60 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <HandHeart className="w-5 h-5 text-[#23483A]" />
            <span className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-widest">
              {t('family.helpSomeoneElse')}
            </span>
          </div>
          <span className="text-[10px] font-mono text-[#536A72]">
            Community Safety Mesh
          </span>
        </div>

        {/* Action: REPORT SOMEONE AS SAFE */}
        <Card className="p-5 bg-[#FAF9F3] border-2 border-[#23483A]/40 space-y-3 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h4 className="text-base font-heading font-bold text-[#202622] flex items-center">
                <HeartHandshake className="w-5 h-5 text-[#23483A] mr-2" />
                {t('family.reportSomeoneSafe')}
              </h4>
              <p className="text-xs text-[#536A72] mt-0.5 leading-relaxed font-medium">
                Encountered a neighbor, friend, or stranger during evacuation? Log a safety report on their behalf.
              </p>
            </div>

            <button
              onClick={() => setIsReportSomeoneOpen(true)}
              className="px-5 py-2.5 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-xs hover:bg-[#1b382d] transition-colors flex items-center space-x-1.5 shadow-md cursor-pointer shrink-0 tactile-press"
            >
              <HeartHandshake className="w-4 h-4" />
              <span>{t('family.reportSomeoneSafe')}</span>
            </button>
          </div>
        </Card>

        {/* List of Community Safety Reports Logged */}
        {communityReports.length > 0 && (
          <div className="space-y-2 pt-1">
            <span className="text-[11px] font-mono text-[#536A72] uppercase block">
              Recent Community Safety Reports ({communityReports.length}):
            </span>
            {communityReports.map((rep) => (
              <Card key={rep.id} className="p-3 bg-[#F4F1E8] border-[#C7B89B] text-xs font-mono flex items-center justify-between">
                <div className="flex items-center space-x-2 text-[#202622]">
                  <CheckCircle2 className="w-4 h-4 text-[#23483A] shrink-0" />
                  <div>
                    <strong className="text-[#202622]">{rep.name}</strong>
                    <span className="text-[#536A72] text-[11px] block">
                      {rep.context} &bull; 📍 {rep.location}
                    </span>
                  </div>
                </div>
                <span className="text-[10px] text-[#536A72] shrink-0">
                  {rep.timestamp}
                </span>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* MODAL 1: CHECK IN SOMEONE WITH ME */}
      {isCheckInOthersOpen && (
        <ModalPortal onClose={() => setIsCheckInOthersOpen(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="check-in-others-title"
            onClick={() => setIsCheckInOthersOpen(false)}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#202622]/70 backdrop-blur-sm font-sans animate-fade-in"
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md bg-[#FAF9F3] border-2 border-[#23483A] rounded-3xl p-6 shadow-2xl space-y-4"
            >
              <div className="flex items-start justify-between pb-3 border-b border-[#C7B89B]/50">
                <div className="flex items-center space-x-2.5">
                  <UserCheck className="w-5 h-5 text-[#23483A]" />
                  <h3 id="check-in-others-title" className="text-base font-heading font-bold text-[#202622]">
                    {t('family.checkInOthers')}
                  </h3>
                </div>
                <button
                  onClick={() => setIsCheckInOthersOpen(false)}
                  aria-label="Close modal"
                  className="p-1 rounded-xl text-[#536A72] hover:text-[#202622] cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <p className="text-xs text-[#536A72]">
                {t('family.selectMembers')}
              </p>

              <div className="space-y-2 max-h-60 overflow-y-auto pt-1">
                {familyList
                  .filter((m) => !m.isSelf)
                  .map((m) => (
                    <label
                      key={m.id}
                      className={`flex items-center justify-between p-3 rounded-xl border transition-colors cursor-pointer ${
                        selectedForCheckIn.includes(m.id)
                          ? 'bg-[#23483A]/10 border-[#23483A] text-[#23483A]'
                          : 'bg-[#F4F1E8] border-[#C7B89B]/50 text-[#202622]'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={selectedForCheckIn.includes(m.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedForCheckIn((prev) => [...prev, m.id]);
                            } else {
                              setSelectedForCheckIn((prev) => prev.filter((id) => id !== m.id));
                            }
                          }}
                          className="w-4 h-4 accent-[#23483A] rounded cursor-pointer"
                        />
                        <div>
                          <strong className="text-xs font-heading font-bold block">{m.name}</strong>
                          <span className="text-[10px] font-mono text-[#536A72]">{m.relationship}</span>
                        </div>
                      </div>

                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white/60">
                        {m.status === 'CHECKED_IN' ? 'Safe' : 'Needs Check-in'}
                      </span>
                    </label>
                  ))}
              </div>

              <button
                onClick={handleConfirmCheckInOthers}
                disabled={selectedForCheckIn.length === 0}
                className={`w-full py-3 px-4 rounded-xl font-heading font-bold text-xs transition-colors cursor-pointer shadow-md ${
                  selectedForCheckIn.length > 0
                    ? 'bg-[#23483A] text-[#FAF9F3] hover:bg-[#1b382d]'
                    : 'bg-[#C7B89B]/50 text-[#536A72] cursor-not-allowed'
                }`}
              >
                {t('family.confirmSafe')} ({selectedForCheckIn.length})
              </button>
            </div>
          </div>
        </ModalPortal>
      )}

      {/* MODAL 2: ADD FAMILY MEMBER */}
      {isAddMemberOpen && (
        <ModalPortal onClose={() => setIsAddMemberOpen(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="add-member-title"
            onClick={() => setIsAddMemberOpen(false)}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#202622]/70 backdrop-blur-sm font-sans animate-fade-in"
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md bg-[#FAF9F3] border-2 border-[#23483A] rounded-3xl p-6 shadow-2xl space-y-4"
            >
              <div className="flex items-start justify-between pb-3 border-b border-[#C7B89B]/50">
                <div className="flex items-center space-x-2.5">
                  <UserPlus className="w-5 h-5 text-[#23483A]" />
                  <h3 id="add-member-title" className="text-base font-heading font-bold text-[#202622]">
                    {t('family.addMemberTitle')}
                  </h3>
                </div>
                <button
                  onClick={() => setIsAddMemberOpen(false)}
                  aria-label="Close modal"
                  className="p-1 rounded-xl text-[#536A72] hover:text-[#202622] cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleAddMemberSubmit} className="space-y-3">
                <div>
                  <label className="text-xs font-mono font-bold text-[#536A72] block mb-1">
                    {t('family.nameLabel')}
                  </label>
                  <input
                    type="text"
                    required
                    value={newMemberName}
                    onChange={(e) => setNewMemberName(e.target.value)}
                    placeholder="e.g. Grandma Devi"
                    className="w-full px-3.5 py-2 rounded-xl bg-white border border-[#C7B89B] text-xs text-[#202622] focus:outline-none focus:border-[#23483A]"
                  />
                </div>

                <div>
                  <label className="text-xs font-mono font-bold text-[#536A72] block mb-1">
                    {t('family.relationshipLabel')}
                  </label>
                  <select
                    value={newMemberRel}
                    onChange={(e) => setNewMemberRel(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-white border border-[#C7B89B] text-xs text-[#202622] focus:outline-none focus:border-[#23483A]"
                  >
                    <option value="Spouse">Spouse</option>
                    <option value="Son">Son</option>
                    <option value="Daughter">Daughter</option>
                    <option value="Father">Father</option>
                    <option value="Mother">Mother</option>
                    <option value="Grandparent">Grandparent</option>
                    <option value="Relative">Relative</option>
                  </select>
                </div>

                <div className="pt-2 flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setIsAddMemberOpen(false)}
                    className="px-4 py-2 rounded-xl bg-[#F4F1E8] border border-[#C7B89B] text-[#536A72] font-heading font-bold text-xs cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-xs hover:bg-[#1b382d] cursor-pointer shadow-sm"
                  >
                    {t('family.addMemberTitle')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </ModalPortal>
      )}

      {/* MODAL 3: REPORT SOMEONE AS SAFE (Guided Flow for Non-Family / Community Encounter) */}
      {isReportSomeoneOpen && (
        <ModalPortal onClose={() => setIsReportSomeoneOpen(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="report-someone-title"
            onClick={() => setIsReportSomeoneOpen(false)}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#202622]/70 backdrop-blur-sm font-sans animate-fade-in"
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg bg-[#FAF9F3] border-2 border-[#23483A] rounded-3xl p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto"
            >
              
              <div className="flex items-start justify-between pb-3 border-b border-[#C7B89B]/50">
                <div className="flex items-center space-x-2.5">
                  <HeartHandshake className="w-6 h-6 text-[#23483A]" />
                  <div>
                    <span className="text-[10px] font-mono font-bold text-[#23483A] uppercase tracking-widest block">
                      COMMUNITY SAFETY CONFIRMATION
                    </span>
                    <h3 id="report-someone-title" className="text-base font-heading font-bold text-[#202622]">
                      {t('family.reportSomeoneTitle')}
                    </h3>
                  </div>
                </div>
                <button
                  onClick={() => setIsReportSomeoneOpen(false)}
                  aria-label="Close modal"
                  className="p-1 rounded-xl text-[#536A72] hover:text-[#202622] cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleReportSomeoneSubmit} className="space-y-3.5">
                {/* Field 1: Optional Name */}
                <div>
                  <label className="text-xs font-mono font-bold text-[#536A72] block mb-1">
                    1. {t('family.personNameOpt')}
                  </label>
                  <input
                    type="text"
                    value={reportPersonName}
                    onChange={(e) => setReportPersonName(e.target.value)}
                    placeholder="e.g. Ramesh or Unidentified elderly person"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#C7B89B] text-xs text-[#202622] focus:outline-none focus:border-[#23483A]"
                  />
                  <span className="text-[10px] text-[#536A72] mt-0.5 block">
                    Leave blank if person's name is unknown.
                  </span>
                </div>

                {/* Field 2: Relationship / Context */}
                <div>
                  <label className="text-xs font-mono font-bold text-[#536A72] block mb-1">
                    2. {t('family.contextLabel')}
                  </label>
                  <select
                    value={reportContext}
                    onChange={(e) => setReportContext(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-white border border-[#C7B89B] text-xs font-semibold text-[#202622] focus:outline-none focus:border-[#23483A]"
                  >
                    <option value="Someone I Encountered">{t('family.contextEncountered')}</option>
                    <option value="Neighbor">{t('family.contextNeighbor')}</option>
                    <option value="Friend">{t('family.contextFriend')}</option>
                    <option value="Family Member">{t('family.contextFamily')}</option>
                    <option value="Unknown / Stranger">{t('family.contextUnknown')}</option>
                  </select>
                </div>

                {/* Field 3: Location */}
                <div>
                  <label className="text-xs font-mono font-bold text-[#536A72] block mb-1 flex items-center">
                    <MapPin className="w-3.5 h-3.5 text-[#23483A] mr-1" />
                    3. {t('family.locationLabel')}
                  </label>
                  <input
                    type="text"
                    required
                    value={reportLocation}
                    onChange={(e) => setReportLocation(e.target.value)}
                    placeholder="e.g. Guwahati Sector 4 Shelter B"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-[#C7B89B] text-xs text-[#202622] focus:outline-none focus:border-[#23483A]"
                  />
                </div>

                {/* Field 4: Confirmation Checkbox */}
                <div className="p-3 rounded-xl bg-[#23483A]/10 border border-[#23483A]/30">
                  <label className="flex items-start space-x-2.5 cursor-pointer">
                    <input
                      type="checkbox"
                      required
                      checked={isConfirmedSafe}
                      onChange={(e) => setIsConfirmedSafe(e.target.checked)}
                      className="w-4 h-4 accent-[#23483A] rounded mt-0.5 cursor-pointer shrink-0"
                    />
                    <span className="text-xs font-medium text-[#202622] leading-snug">
                      {t('family.confirmNotice')}
                    </span>
                  </label>
                </div>

                {/* Action Buttons */}
                <div className="pt-2 flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setIsReportSomeoneOpen(false)}
                    className="px-4 py-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B] text-[#536A72] font-heading font-bold text-xs cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!isConfirmedSafe}
                    className={`px-5 py-2.5 rounded-xl font-heading font-bold text-xs transition-colors shadow-md cursor-pointer ${
                      isConfirmedSafe
                        ? 'bg-[#23483A] text-[#FAF9F3] hover:bg-[#1b382d]'
                        : 'bg-[#C7B89B]/50 text-[#536A72] cursor-not-allowed'
                    }`}
                  >
                    {t('family.confirmTheyAreSafe')}
                  </button>
                </div>
              </form>

            </div>
          </div>
        </ModalPortal>
      )}

    </div>
  );
};
