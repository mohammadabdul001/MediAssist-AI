// Mock API calls for role-based authentication
const users = [
  {
    id: 1,
    email: "admin123@gmail.com",
    password: "Pr@1245",
    role: "admin",
    name: "Admin",
    createdAt: "2024-01-01T00:00:00.000Z"
  },
  {
    id: 2,
    email: "patient@example.com",
    password: "patient123",
    role: "patient",
    name: "Rajesh",
    phone: "+1234567890",
    dateOfBirth: "1990-05-15",
    bloodGroup: "O+",
    createdAt: "2024-01-02T00:00:00.000Z"
  },
  {
    id: 3,
    email: "doctor@example.com",
    password: "doctor123",
    role: "doctor",
    name: "Dr. Sarah Reddy",
    specialization: "Cardiology",
    license: "MD12345",
    phone: "+1234567891",
    createdAt: "2024-01-03T00:00:00.000Z"
  },
  {
    id: 4,
    email: "lab@example.com",
    password: "lab123",
    role: "lab_person",
    name: "Ramesh",
    labName: "Central Lab",
    phone: "+1234567892",
    createdAt: "2024-01-04T00:00:00.000Z"
  },
  {
    id: 5,
    email: "pharmacy@example.com",
    password: "pharmacy123",
    role: "pharmacy",
    name: "Ramu",
    pharmacyName: "MediCare Pharmacy",
    phone: "+1234567893",
    createdAt: "2024-01-05T00:00:00.000Z"
  }
];

export const login = async (email, password) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const user = users.find(u => u.email === email && u.password === password);
      if (user) {
        const { password: _, ...userWithoutPassword } = user;
        resolve({ 
          ...userWithoutPassword, 
          token: `fake-jwt-token-${user.id}` 
        });
      } else {
        reject(new Error('Invalid credentials'));
      }
    }, 500);
  });
};

export const register = async (userData) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const existingUser = users.find(u => u.email === userData.email);
      if (existingUser) {
        reject(new Error('User already exists'));
        return;
      }
      
      const newUser = {
        id: users.length + 1,
        ...userData,
        createdAt: new Date().toISOString()
      };
      
      users.push(newUser);
      const { password: _, ...userWithoutPassword } = newUser;
      resolve({ 
        ...userWithoutPassword, 
        token: `fake-jwt-token-${newUser.id}` 
      });
    }, 500);
  });
};

export const getStats = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ 
        totalUsers: users.length, 
        doctors: users.filter(u => u.role === 'doctor').length,
        patients: users.filter(u => u.role === 'patient').length,
        labPersonnel: users.filter(u => u.role === 'lab_person').length,
        pharmacies: users.filter(u => u.role === 'pharmacy').length,
        systemHealth: '99.9%' 
      });
    }, 300);
  });
};

export const getPatients = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(users.filter(u => u.role === 'patient'));
    }, 300);
  });
};

export const getLabTests = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        {
          id: 1,
          patientName: "John Doe",
          testName: "Blood Test",
          status: "pending",
          requestedDate: "2024-01-10T00:00:00.000Z",
          results: null,
          images: []
        }
      ]);
    }, 300);
  });
};

export const getPrescriptions = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        {
          id: 1,
          patientName: "Rajesh",
          doctorName: "Dr. Sarah Reddy",
          medications: [
            {
              name: "Aspirin",
              dosage: "100mg",
              frequency: "Once daily",
              duration: "7 days"
            }
          ],
          prescribedDate: "2024-01-10T00:00:00.000Z",
          status: "pending"
        }
      ]);
    }, 300);
  });
};