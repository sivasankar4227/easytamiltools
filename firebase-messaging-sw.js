importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.1/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyCoX1UtTl1LFGBvWpjfMt4hh_6nNSZqedo",
  authDomain: "easytamiltools2026.firebaseapp.com",
  projectId: "easytamiltools2026",
  storageBucket: "easytamiltools2026.firebasestorage.app",
  messagingSenderId: "508760317744",
  appId: "1:508760317744:web:6dbc1fbaab7ff761e3b2f5",
  measurementId: "G-JS66CK5D16"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  self.registration.showNotification(payload.notification.title, {
    body: payload.notification.body,
    icon: "/static/logo.png"
  });
});