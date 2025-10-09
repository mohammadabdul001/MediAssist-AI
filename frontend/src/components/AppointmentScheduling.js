import React, { useState, useContext } from 'react';
import { useAppContext } from '../context/AppContext';
import { motion } from 'framer-motion';

const AppointmentScheduling = () => {
  const { t } = useAppContext();
  const [activeTab, setActiveTab] = useState('book');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [selectedSpecialty, setSelectedSpecialty] = useState('');
  const [appointmentReason, setAppointmentReason] = useState('');

  const [appointments, setAppointments] = useState([
    {
      id: 1,
      doctor: 'Dr. Sarah Johnson',
      specialty: 'Cardiology',
      date: '2024-01-20',
      time: '10:00 AM',
      status: 'Confirmed',
      reason: 'Follow-up consultation'
    },
    {
      id: 2,
      doctor: 'Dr. Michael Chen',
      specialty: 'Dermatology',
      date: '2024-01-25',
      time: '2:30 PM',
      status: 'Pending',
      reason: 'Skin rash evaluation'
    }
  ]);

  const doctors = [
    { id: 1, name: 'Dr. Sarah Johnson', specialty: 'Cardiology', available: true },
    { id: 2, name: 'Dr. Michael Chen', specialty: 'Dermatology', available: true },
    { id: 3, name: 'Dr. Emily Davis', specialty: 'Pediatrics', available: true },
    { id: 4, name: 'Dr. Robert Wilson', specialty: 'Orthopedics', available: false },
    { id: 5, name: 'Dr. Lisa Martinez', specialty: 'Neurology', available: true }
  ];

  const specialties = [
    'Cardiology', 'Dermatology', 'Pediatrics', 'Orthopedics', 'Neurology',
    'Oncology', 'Psychiatry', 'Ophthalmology', 'ENT', 'General Medicine'
  ];

  const timeSlots = [
    '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
    '2:00 PM', '2:30 PM', '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM'
  ];

  const bookAppointment = () => {
    if (selectedDate && selectedTime && selectedDoctor && appointmentReason) {
      const doctor = doctors.find(d => d.id === parseInt(selectedDoctor));
      const newAppointment = {
        id: appointments.length + 1,
        doctor: doctor.name,
        specialty: doctor.specialty,
        date: selectedDate,
        time: selectedTime,
        status: 'Pending',
        reason: appointmentReason
      };
      setAppointments([...appointments, newAppointment]);
      
      // Reset form
      setSelectedDate('');
      setSelectedTime('');
      setSelectedDoctor('');
      setSelectedSpecialty('');
      setAppointmentReason('');
    }
  };

  const cancelAppointment = (id) => {
    setAppointments(appointments.filter(apt => apt.id !== id));
  };

  const rescheduleAppointment = (id) => {
    // Implementation for rescheduling
    console.log('Reschedule appointment:', id);
  };

  return (
    <div className="appointment-scheduling">
      <div className="appointment-container">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="appointment-title"
        >
          📅 Appointment Scheduling
        </motion.h2>

        <div className="appointment-tabs">
          <button
            className={`tab ${activeTab === 'book' ? 'active' : ''}`}
            onClick={() => setActiveTab('book')}
          >
            Book Appointment
          </button>
          <button
            className={`tab ${activeTab === 'my-appointments' ? 'active' : ''}`}
            onClick={() => setActiveTab('my-appointments')}
          >
            My Appointments
          </button>
          <button
            className={`tab ${activeTab === 'doctors' ? 'active' : ''}`}
            onClick={() => setActiveTab('doctors')}
          >
            Available Doctors
          </button>
        </div>

        <div className="appointment-content">
          {activeTab === 'book' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="book-appointment"
            >
              <h3>Book New Appointment</h3>
              
              <div className="booking-form">
                <div className="form-row">
                  <div className="form-group">
                    <label>Specialty</label>
                    <select
                      value={selectedSpecialty}
                      onChange={(e) => setSelectedSpecialty(e.target.value)}
                    >
                      <option value="">Select specialty...</option>
                      {specialties.map(specialty => (
                        <option key={specialty} value={specialty}>{specialty}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label>Doctor</label>
                    <select
                      value={selectedDoctor}
                      onChange={(e) => setSelectedDoctor(e.target.value)}
                      disabled={!selectedSpecialty}
                    >
                      <option value="">Select doctor...</option>
                      {doctors
                        .filter(d => !selectedSpecialty || d.specialty === selectedSpecialty)
                        .map(doctor => (
                          <option key={doctor.id} value={doctor.id}>
                            {doctor.name} - {doctor.specialty}
                          </option>
                        ))}
                    </select>
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Date</label>
                    <input
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      min={new Date().toISOString().split('T')[0]}
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Time</label>
                    <select
                      value={selectedTime}
                      onChange={(e) => setSelectedTime(e.target.value)}
                    >
                      <option value="">Select time...</option>
                      {timeSlots.map(time => (
                        <option key={time} value={time}>{time}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>Reason for Visit</label>
                  <textarea
                    value={appointmentReason}
                    onChange={(e) => setAppointmentReason(e.target.value)}
                    placeholder="Describe your symptoms or reason for the appointment..."
                    rows="4"
                  />
                </div>

                <button 
                  onClick={bookAppointment}
                  disabled={!selectedDate || !selectedTime || !selectedDoctor || !appointmentReason}
                  className="btn-primary"
                >
                  Book Appointment
                </button>
              </div>
            </motion.div>
          )}

          {activeTab === 'my-appointments' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="my-appointments"
            >
              <h3>My Appointments</h3>
              
              <div className="appointments-list">
                {appointments.length === 0 ? (
                  <p className="no-appointments">No appointments scheduled</p>
                ) : (
                  appointments.map(appointment => (
                    <motion.div
                      key={appointment.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="appointment-item"
                    >
                      <div className="appointment-header">
                        <span className="appointment-doctor">{appointment.doctor}</span>
                        <span className={`appointment-status ${appointment.status.toLowerCase()}`}>
                          {appointment.status}
                        </span>
                      </div>
                      
                      <div className="appointment-details">
                        <p><strong>Specialty:</strong> {appointment.specialty}</p>
                        <p><strong>Date:</strong> {appointment.date}</p>
                        <p><strong>Time:</strong> {appointment.time}</p>
                        <p><strong>Reason:</strong> {appointment.reason}</p>
                      </div>
                      
                      <div className="appointment-actions">
                        <button 
                          onClick={() => rescheduleAppointment(appointment.id)}
                          className="btn-secondary"
                        >
                          📅 Reschedule
                        </button>
                        <button 
                          onClick={() => cancelAppointment(appointment.id)}
                          className="btn-danger"
                        >
                          ❌ Cancel
                        </button>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          )}

          {activeTab === 'doctors' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="available-doctors"
            >
              <h3>Available Doctors</h3>
              
              <div className="doctors-grid">
                {doctors.map(doctor => (
                  <motion.div
                    key={doctor.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="doctor-card"
                  >
                    <div className="doctor-avatar">
                      👨‍⚕️
                    </div>
                    <div className="doctor-info">
                      <h4>{doctor.name}</h4>
                      <p className="doctor-specialty">{doctor.specialty}</p>
                      <span className={`doctor-status ${doctor.available ? 'available' : 'unavailable'}`}>
                        {doctor.available ? '🟢 Available' : '🔴 Unavailable'}
                      </span>
                    </div>
                    <div className="doctor-actions">
                      <button 
                        className="btn-primary"
                        disabled={!doctor.available}
                      >
                        Book Appointment
                      </button>
                      <button className="btn-secondary">View Profile</button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AppointmentScheduling; 