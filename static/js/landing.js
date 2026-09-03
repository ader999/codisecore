/**
 * Codice路 - Landing Page & Plantilla Oficial
 * Interactividad: Modales, Registro de Notificación, Tabs Legales y Selector de Ciudades
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Detección de Scroll para el Header
  const header = document.querySelector('.site-header');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      header?.classList.add('scrolled');
    } else {
      header?.classList.remove('scrolled');
    }
  });

  // 2. Menú Móvil
  const menuToggle = document.getElementById('mobileMenuToggle');
  const mainNav = document.getElementById('mainNav');
  if (menuToggle && mainNav) {
    menuToggle.addEventListener('click', () => {
      mainNav.classList.toggle('active');
    });

    // Cerrar al hacer clic en enlaces
    mainNav.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => mainNav.classList.remove('active'));
    });
  }

  // 3. Sistema de Notificaciones Toast
  function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let iconSvg = '';
    if (type === 'success') {
      iconSvg = `<svg width="20" height="20" fill="none" stroke="#10b981" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`;
    } else {
      iconSvg = `<svg width="20" height="20" fill="none" stroke="#f59e0b" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`;
    }

    toast.innerHTML = `${iconSvg} <span>${message}</span>`;
    container.appendChild(toast);

    // Animación de entrada
    setTimeout(() => toast.classList.add('active'), 20);

    // Auto cierre
    setTimeout(() => {
      toast.classList.remove('active');
      setTimeout(() => toast.remove(), 400);
    }, 4000);
  }

  // 4. Sistema Centralizado de Modales
  const openModalBtns = document.querySelectorAll('[data-open-modal]');
  const closeModalBtns = document.querySelectorAll('[data-close-modal]');
  const modals = document.querySelectorAll('.modal-backdrop');

  function openModal(modalId) {
    const targetModal = document.getElementById(modalId);
    if (targetModal) {
      targetModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal(modalElement) {
    if (modalElement) {
      modalElement.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  openModalBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-open-modal');
      openModal(targetId);

      // Si el botón especifica una pestaña a activar dentro del modal legal
      const targetTab = btn.getAttribute('data-target-tab');
      if (targetTab) {
        switchLegalTab(targetTab);
      }
    });
  });

  closeModalBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const parentModal = btn.closest('.modal-backdrop');
      closeModal(parentModal);
    });
  });

  // Cerrar al hacer click en el backdrop oscuro
  modals.forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal);
      }
    });
  });

  // Cerrar con la tecla Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      modals.forEach(modal => {
        if (modal.classList.contains('active')) {
          closeModal(modal);
        }
      });
    }
  });

  // 5. Pestañas Legales (Términos vs Privacidad)
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');

  function switchLegalTab(tabId) {
    tabButtons.forEach(b => b.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));

    const activeBtn = document.querySelector(`[data-tab="${tabId}"]`);
    const activeContent = document.getElementById(tabId);

    if (activeBtn && activeContent) {
      activeBtn.classList.add('active');
      activeContent.classList.add('active');
    }
  }

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchLegalTab(tabId);
    });
  });

  // 6. Formularios de Pre-registro / Notificación Temprana
  const notifyForms = document.querySelectorAll('.notify-form, #modalNotifyForm');
  notifyForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = form.querySelector('input[type="email"]');
      if (input && input.value) {
        const email = input.value.trim();
        try {
          const registered = JSON.parse(localStorage.getItem('codice_subscribers') || '[]');
          if (!registered.includes(email)) {
            registered.push(email);
            localStorage.setItem('codice_subscribers', JSON.stringify(registered));
          }
          showToast(`¡Excelente! Te notificaremos a ${email} en cuanto Codice路 esté disponible.`, 'success');
          input.value = '';
          
          // Si estaba dentro de un modal, cerrarlo tras 1.5s
          const parentModal = form.closest('.modal-backdrop');
          if (parentModal) {
            setTimeout(() => closeModal(parentModal), 1200);
          }
        } catch (err) {
          showToast(`¡Gracias! Hemos registrado ${email} para el lanzamiento.`, 'success');
          input.value = '';
        }
      }
    });
  });

  // 7. Interacción con tarjetas de Ciudades
  const cityCards = document.querySelectorAll('.city-card');
  cityCards.forEach(card => {
    card.addEventListener('click', () => {
      const cityName = card.querySelector('.city-name')?.textContent || 'esta ciudad';
      const cityTagline = card.querySelector('.city-tagline')?.textContent || '';
      showToast(`Ciudad Creativa: ${cityName} — ${cityTagline}`, 'info');
    });
  });

  // 8. Botón Copiar Enlace API
  const copyApiBtn = document.getElementById('copyApiBtn');
  if (copyApiBtn) {
    copyApiBtn.addEventListener('click', () => {
      const apiUrl = `${window.location.origin}/api/`;
      navigator.clipboard.writeText(apiUrl).then(() => {
        showToast('Enlace de la API copiado al portapapeles: /api/', 'success');
      }).catch(() => {
        showToast('Ruta de la API: /api/', 'info');
      });
    });
  }

  // 9. Detección de Hash y Ruta en URL (ej: /terminos/, /privacidad/, #terminos, #privacidad)
  function checkUrlHash() {
    const hash = window.location.hash.toLowerCase();
    const path = window.location.pathname.toLowerCase();

    if (hash === '#terminos' || hash === '#condiciones' || path.startsWith('/terminos')) {
      openModal('legalModal');
      switchLegalTab('terminosApp');
    } else if (hash === '#privacidad' || hash === '#uso' || path.startsWith('/privacidad')) {
      openModal('legalModal');
      switchLegalTab('privacidadApp');
    } else if (hash === '#playstore' || hash === '#descarga-playstore') {
      openModal('playStoreModal');
    } else if (hash === '#apk' || hash === '#descarga-apk') {
      openModal('apkModal');
    }
  }
  
  checkUrlHash();
  window.addEventListener('hashchange', checkUrlHash);
});
