import { useEffect } from 'react';
import { setProfile, setBackend, setSavedUrls, setAutomation } from '@/stores/appStore.js';
import api from '@/lib/api.js';

export default function AppInitializer() {
  useEffect(() => {
    // Load persisted profile
    api.getProfile()
      .then((profile) => {
        setProfile(profile);
      })
      .catch(() => {});

    // Load saved URLs
    api.getSaved()
      .then((data) => {
        const urls = (data.jobs || []).map((j) => j.url).filter(Boolean);
        setSavedUrls(urls);
      })
      .catch(() => {});

    // Load backend info
    api.getBackends()
      .then((data) => {
        setBackend(data);
      })
      .catch(() => {});

    // Load automation status
    api.getAutomationStatus()
      .then((status) => {
        api.getAutomationLogs()
          .then((logs) => {
            setAutomation({ ...status, logs: logs.logs });
          })
          .catch(() => {
            setAutomation(status);
          });
      })
      .catch(() => {});
  }, []);

  return null;
}
