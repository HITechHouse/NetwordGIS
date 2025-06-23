import React, { useState, useEffect, useContext, createContext } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import './App.css';
import { 
  MapIcon, 
  PlusIcon, 
  UserIcon, 
  ChartBarIcon, 
  CogIcon,
  PowerIcon,
  BuildingOfficeIcon,
  TruckIcon,
  WifiIcon,
  WrenchScrewdriverIcon,
  HomeIcon
} from '@heroicons/react/24/outline';

// Fix for default markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

// Custom Icons for different infrastructure types
const createCustomIcon = (color, type) => {
  const iconHtml = `
    <div style="
      background-color: ${color};
      width: 25px;
      height: 25px;
      border-radius: 50%;
      border: 2px solid white;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: bold;
      font-size: 12px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    ">
      ${type.charAt(0).toUpperCase()}
    </div>
  `;
  
  return L.divIcon({
    html: iconHtml,
    className: 'custom-marker',
    iconSize: [25, 25],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });
};

// Color mapping for infrastructure types
const getColorByType = (type) => {
  const colors = {
    electricity: '#f59e0b',
    water: '#3b82f6',
    sewage: '#8b5cf6',
    telecommunications: '#10b981',
    roads: '#6b7280',
    public_facilities: '#ef4444'
  };
  return colors[type] || '#6b7280';
};

// Infrastructure type translations
const infraTypes = {
  electricity: 'كهرباء',
  water: 'مياه',
  sewage: 'صرف صحي',
  telecommunications: 'اتصالات',
  roads: 'طرق',
  public_facilities: 'مرافق عامة'
};

const statusTypes = {
  operational: 'يعمل',
  damaged: 'معطل',
  under_maintenance: 'تحت الصيانة',
  needs_repair: 'يحتاج إصلاح'
};

const conditionTypes = {
  excellent: 'ممتاز',
  good: 'جيد',
  fair: 'مقبول',
  poor: 'ضعيف',
  critical: 'حرج'
};

const roleTypes = {
  municipality: 'بلدية',
  directorate: 'مديرية',
  ministry: 'وزارة'
};

// Login Component
const Login = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    role: 'municipality',
    city: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const response = await axios.post(`${API}${endpoint}`, formData);
      
      if (isLogin) {
        localStorage.setItem('token', response.data.token);
        onLogin(response.data.user, response.data.token);
      } else {
        setIsLogin(true);
        setError('تم إنشاء الحساب بنجاح، يرجى تسجيل الدخول');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'حدث خطأ في العملية');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <MapIcon className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">نظام إدارة البنية التحتية</h1>
          <p className="text-gray-600 mt-2">المدن السورية - نظم المعلومات الجغرافية</p>
        </div>

        <div className="mb-6">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
              }`}
            >
              تسجيل الدخول
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                !isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
              }`}
            >
              حساب جديد
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">اسم المستخدم</label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required={!isLogin}
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">البريد الإلكتروني</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">كلمة المرور</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({...formData, password: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {!isLogin && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الدور</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="municipality">بلدية</option>
                  <option value="directorate">مديرية</option>
                  <option value="ministry">وزارة</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">المدينة</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({...formData, city: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="اختياري للوزارة والمديرية"
                />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'جاري التحميل...' : (isLogin ? 'تسجيل الدخول' : 'إنشاء حساب')}
          </button>
        </form>
      </div>
    </div>
  );
};

// Add Infrastructure Modal
const AddInfrastructureModal = ({ isOpen, onClose, onAdd, clickedCoordinates }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'electricity',
    subtype: '',
    status: 'operational',
    condition: 'good',
    city: '',
    district: '',
    description: '',
    coordinates: clickedCoordinates || [0, 0]
  });

  useEffect(() => {
    if (clickedCoordinates) {
      setFormData(prev => ({ ...prev, coordinates: clickedCoordinates }));
    }
  }, [clickedCoordinates]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await onAdd(formData);
      onClose();
      setFormData({
        name: '',
        type: 'electricity',
        subtype: '',
        status: 'operational',
        condition: 'good',
        city: '',
        district: '',
        description: '',
        coordinates: [0, 0]
      });
    } catch (error) {
      console.error('Error adding infrastructure:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900">إضافة عنصر بنية تحتية</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الاسم</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">النوع</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(infraTypes).map(([key, value]) => (
                    <option key={key} value={key}>{value}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">النوع الفرعي</label>
                <input
                  type="text"
                  value={formData.subtype}
                  onChange={(e) => setFormData({...formData, subtype: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الحالة</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({...formData, status: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(statusTypes).map(([key, value]) => (
                    <option key={key} value={key}>{value}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">الجودة</label>
                <select
                  value={formData.condition}
                  onChange={(e) => setFormData({...formData, condition: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(conditionTypes).map(([key, value]) => (
                    <option key={key} value={key}>{value}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">المدينة</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({...formData, city: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">المنطقة</label>
                <input
                  type="text"
                  value={formData.district}
                  onChange={(e) => setFormData({...formData, district: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">الوصف</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">خط الطول</label>
                <input
                  type="number"
                  step="any"
                  value={formData.coordinates[0]}
                  onChange={(e) => setFormData({...formData, coordinates: [parseFloat(e.target.value), formData.coordinates[1]]})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">خط العرض</label>
                <input
                  type="number"
                  step="any"
                  value={formData.coordinates[1]}
                  onChange={(e) => setFormData({...formData, coordinates: [formData.coordinates[0], parseFloat(e.target.value)]})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 space-x-reverse pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium"
              >
                إلغاء
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
              >
                إضافة
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Map Component with click handler
const MapClickHandler = ({ onMapClick }) => {
  const map = useMap();
  
  useEffect(() => {
    const handleClick = (e) => {
      onMapClick([e.latlng.lng, e.latlng.lat]);
    };
    
    map.on('click', handleClick);
    
    return () => {
      map.off('click', handleClick);
    };
  }, [map, onMapClick]);
  
  return null;
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [infrastructureData, setInfrastructureData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [selectedType, setSelectedType] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [clickedCoordinates, setClickedCoordinates] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  // Initialize axios with token
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserData();
    }
  }, [token]);

  const fetchUserData = async () => {
    try {
      const response = await axios.get(`${API}/infrastructure`);
      // If successful, user is authenticated
      fetchInfrastructure();
      fetchAnalytics();
    } catch (error) {
      console.error('Token invalid:', error);
      logout();
    }
  };

  const fetchInfrastructure = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/infrastructure`);
      setInfrastructureData(response.data);
      setFilteredData(response.data);
    } catch (error) {
      console.error('Error fetching infrastructure:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics/overview`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const handleLogin = (userData, userToken) => {
    setUser(userData);
    setToken(userToken);
    localStorage.setItem('token', userToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${userToken}`;
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  const handleAddInfrastructure = async (formData) => {
    try {
      const response = await axios.post(`${API}/infrastructure`, formData);
      setInfrastructureData([...infrastructureData, response.data]);
      applyFilters([...infrastructureData, response.data]);
      fetchAnalytics();
    } catch (error) {
      console.error('Error adding infrastructure:', error);
      throw error;
    }
  };

  const applyFilters = (data = infrastructureData) => {
    let filtered = data;
    
    if (selectedType !== 'all') {
      filtered = filtered.filter(item => item.type === selectedType);
    }
    
    if (selectedStatus !== 'all') {
      filtered = filtered.filter(item => item.status === selectedStatus);
    }
    
    setFilteredData(filtered);
  };

  useEffect(() => {
    applyFilters();
  }, [selectedType, selectedStatus, infrastructureData]);

  const handleMapClick = (coordinates) => {
    setClickedCoordinates(coordinates);
    setShowAddModal(true);
  };

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <AuthContext.Provider value={{ user, token, logout }}>
      <div className="min-h-screen bg-gray-50" dir="rtl">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center ml-3">
                  <MapIcon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">نظام إدارة البنية التحتية</h1>
                  <p className="text-sm text-gray-600">المدن السورية</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4 space-x-reverse">
                <button
                  onClick={() => setShowAddModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md flex items-center space-x-2 space-x-reverse hover:bg-blue-700"
                >
                  <PlusIcon className="w-4 h-4" />
                  <span>إضافة عنصر</span>
                </button>
                
                <div className="flex items-center space-x-2 space-x-reverse">
                  <UserIcon className="w-5 h-5 text-gray-600" />
                  <span className="text-sm text-gray-600">{user?.username}</span>
                  <button
                    onClick={logout}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    تسجيل خروج
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Analytics Cards */}
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">توزيع حسب النوع</h3>
                <div className="space-y-2">
                  {Object.entries(analytics.type_distribution).map(([type, count]) => (
                    <div key={type} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{infraTypes[type]}</span>
                      <span className="text-sm font-medium text-gray-900">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">توزيع حسب الحالة</h3>
                <div className="space-y-2">
                  {Object.entries(analytics.status_distribution).map(([status, count]) => (
                    <div key={status} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{statusTypes[status]}</span>
                      <span className="text-sm font-medium text-gray-900">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">توزيع حسب الجودة</h3>
                <div className="space-y-2">
                  {Object.entries(analytics.condition_distribution).map(([condition, count]) => (
                    <div key={condition} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{conditionTypes[condition]}</span>
                      <span className="text-sm font-medium text-gray-900">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="bg-white rounded-lg shadow mb-6 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">تصفية النتائج</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">النوع</label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">جميع الأنواع</option>
                  {Object.entries(infraTypes).map(([key, value]) => (
                    <option key={key} value={key}>{value}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">الحالة</label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">جميع الحالات</option>
                  {Object.entries(statusTypes).map(([key, value]) => (
                    <option key={key} value={key}>{value}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Map */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="h-96 md:h-[600px]">
              <MapContainer
                center={[33.5138, 36.2765]} // Damascus coordinates
                zoom={10}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                
                <MapClickHandler onMapClick={handleMapClick} />
                
                {filteredData.map((item) => (
                  <Marker
                    key={item.id}
                    position={[item.coordinates[1], item.coordinates[0]]}
                    icon={createCustomIcon(getColorByType(item.type), item.type)}
                  >
                    <Popup>
                      <div className="text-right" dir="rtl">
                        <h4 className="font-bold text-gray-900">{item.name}</h4>
                        <p className="text-sm text-gray-600">النوع: {infraTypes[item.type]}</p>
                        {item.subtype && <p className="text-sm text-gray-600">النوع الفرعي: {item.subtype}</p>}
                        <p className="text-sm text-gray-600">الحالة: {statusTypes[item.status]}</p>
                        <p className="text-sm text-gray-600">الجودة: {conditionTypes[item.condition]}</p>
                        <p className="text-sm text-gray-600">المدينة: {item.city}</p>
                        {item.district && <p className="text-sm text-gray-600">المنطقة: {item.district}</p>}
                        {item.description && <p className="text-sm text-gray-600 mt-2">{item.description}</p>}
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </div>

          {/* Legend */}
          <div className="bg-white rounded-lg shadow p-6 mt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">دليل الألوان</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(infraTypes).map(([type, name]) => (
                <div key={type} className="flex items-center space-x-2 space-x-reverse">
                  <div
                    className="w-4 h-4 rounded-full border-2 border-white shadow"
                    style={{ backgroundColor: getColorByType(type) }}
                  />
                  <span className="text-sm text-gray-700">{name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Add Infrastructure Modal */}
        <AddInfrastructureModal
          isOpen={showAddModal}
          onClose={() => {
            setShowAddModal(false);
            setClickedCoordinates(null);
          }}
          onAdd={handleAddInfrastructure}
          clickedCoordinates={clickedCoordinates}
        />
      </div>
    </AuthContext.Provider>
  );
};

export default App;