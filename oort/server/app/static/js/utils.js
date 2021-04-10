Vue.mixin({
  methods: {
    getFilePath (upload, root_path) {
      return upload.file_path.replace(root_path + '/', '')
    },
    getOrganisationDatasetURL (upload) {
      return 'https://' + upload.organisation.subdomain + '.arcsecond.io/data/' + upload.night_log.date
    },
    getDatasetURL (upload) {
      return (upload.dataset) ? 'https://www.arcsecond.io/datasets/' + upload.dataset.uuid : ''
    },
    getOrganisationNightLogURL (upload) {
      return 'https://' + upload.organisation.subdomain + '.arcsecond.io/nights/' + upload.night_log.date
    },
    getNightLogURL (upload) {
      return (upload.night_log) ? 'https://www.arcsecond.io/nightlogs/' + upload.night_log.uuid : ''
    },
    getProfileURL (upload) {
      return 'https://www.arcsecond.io/@' + upload.astronomer
    },
    getOrganisationURL (upload) {
      return 'https://' + upload.organisation.subdomain + '.arcsecond.io'
    },
    getFormattedSize (bytes, decimals) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const dm = decimals || 2
      const sizes = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
    },
    getStatusStyle (upload) {
      return { color: upload.substatus.toLowerCase().startsWith('skipped') ? 'orange' : 'green' }
    },
    getTimeAgoString (date) {
      if (!date) {
        return ''
      }
      // The replace is needed for Safari to successfully parse the date...
      const seconds = Math.ceil((new Date() - new Date(date.replace(' ', 'T'))) / 1000)
      if (seconds < 60) {
        return 'moments ago'
      } else if (seconds < 3600) {
        return (seconds / 60).toFixed(1).toString() + ' minutes ago'
      } else if (seconds < 3600 * 24) {
        return (seconds / 3600).toFixed(1).toString() + ' hours ago'
      } else {
        return (seconds / 3600 / 24).toFixed(1).toString() + ' days ago'
      }
    }
  }
})

