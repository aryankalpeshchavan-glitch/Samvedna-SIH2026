import React, { useState, useMemo } from 'react';
import useStore from '../../store/useStore';
import { getInitials, getStatusClass, formatDistance } from '../../utils/formatters';

export default function PeopleAtRisk() {
  const persons = useStore((s) => s.persons);
  const selectPerson = useStore((s) => s.selectPerson);
  const addToast = useStore((s) => s.addToast);
  const connected = useStore((s) => s.connected);

  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('ALL');

  const inZoneCount = useMemo(() => persons.filter((p) => p.status === 'IN ZONE').length, [persons]);

  const filtered = useMemo(() => {
    let list = [...persons];
    if (filter !== 'ALL') {
      list = list.filter((p) => p.status === filter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((p) =>
        p.name.toLowerCase().includes(q) ||
        p.profession.toLowerCase().includes(q) ||
        p.phone.includes(q)
      );
    }
    list.sort((a, b) => (a.distanceToImpact || 999) - (b.distanceToImpact || 999));
    return list;
  }, [persons, search, filter]);

  const handleNotifyAll = () => {
    addToast('📱 Sending emergency SMS to all registered persons...');
  };

  return (
    <>
      <div className="panel-section-header">
        <span>People at Risk</span>
        <span className="count">In Zone: {inZoneCount} / {persons.length}</span>
      </div>

      <div className="search-bar">
        <input
          className="search-input"
          type="text"
          placeholder="Search name, phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          id="people-search"
        />
        <select
          className="filter-select"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          id="people-filter"
        >
          <option value="ALL">All</option>
          <option value="IN ZONE">In Zone</option>
          <option value="SAFE">Safe</option>
          <option value="NOTIFIED">Notified</option>
          <option value="EVACUATED">Evacuated</option>
        </select>
      </div>

      <div className="panel-section-body">
        {filtered.map((person) => (
          <div
            key={person.id}
            className="person-row"
            id={`person-${person.id}`}
            onClick={() => selectPerson(person)}
          >
            <div className="avatar">{getInitials(person.name)}</div>
            <div className="person-info">
              <div className="person-name">{person.name}</div>
              <div className="person-detail">{person.profession} · {person.phone}</div>
            </div>
            <div className="person-meta">
              <span className={`status-chip ${getStatusClass(person.status)}`}>
                {person.status}
              </span>
              {person.distanceToImpact != null && (
                <span className="distance-label">
                  {formatDistance(person.distanceToImpact)} away
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div style={{ padding: 8, flexShrink: 0 }}>
        <button className="btn btn-primary btn-block" onClick={handleNotifyAll} id="notify-all-btn">
          📱 Notify All ({persons.length})
        </button>
      </div>
    </>
  );
}
