var app = new Vue({
  el: '#vuejs',
  data: {
    state: {},
    messages: {},
    telescopes: [],
    night_logs: [],
    selected_telescope: null,
    selected_night_log: null,
    selected_night_log_url: '',
    uploads: [],
    filtered_pending_uploads: [],
    filtered_current_uploads: [],
    filtered_finished_uploads: [],
    source: null,
    isAlive: true,
    loopID: null
  },
  beforeDestroy () {
    clearInterval(this.loopID)
  },
  mounted: function () {
    const self = this

    this.source = new EventSource('/uploads')
    this.source.onmessage = function (event) {
      self.isAlive = true
      const json = JSON.parse(event.data)
      self.state = json.state
      self.messages = json.messages

      self.telescopes = json.telescopes
      self.night_logs = json.night_logs || []

      if (self.night_logs.length > 0) {
        self.selected_night_log_url = 'data/' + self.night_logs[0]['date'].replace(/-/gi, '/')
      }

      self.uploads = json.uploads
      self.filtered_pending_uploads = self.uploads.filter(u => u.state === 'pending')
      self.filtered_current_uploads = self.uploads.filter(u => u.state === 'current')
      self.filtered_finished_uploads = self.uploads.filter(u => u.state === 'finished')

      if (self.selected_telescope) {
        self.filtered_pending_uploads = self.filtered_pending_uploads.filter(u => u.telescope['uuid'] === self.selected_telescope['uuid'])
        self.filtered_current_uploads = self.filtered_current_uploads.filter(u => u.telescope['uuid'] === self.selected_telescope['uuid'])
        self.filtered_finished_uploads = self.filtered_finished_uploads.filter(u => u.telescope['uuid'] === self.selected_telescope['uuid'])
      }

      self.filtered_pending_uploads((u1, u2) => new Date(u1.started).getDate() < new Date(u2.started).getDate())
      self.filtered_current_uploads.sort((u1, u2) => new Date(u1.started).getDate() < new Date(u2.started).getDate())
      self.filtered_finished_uploads.sort((u1, u2) => new Date(u1.ended).getDate() < new Date(u2.ended).getDate())

      const bars = document.getElementsByClassName('progress-bar')
      self.filtered_current_uploads.forEach((upload, index) => {
        let bar = bars[index]
        if (bar) {
          bar.style.width = upload.progress.toFixed(1).toString() + '%'
        }
      })
    }

    this.loopID = setInterval(function ping () {
      self.isAlive = (self.source.readyState <= 1)
      if (!self.isAlive) {
        self.$forceUpdate()
      }
    }, 3000)
  },
  methods: {
    selectTelescope (uuid) {
      this.selected_telescope = (uuid === '__all__') ? null : this.telescopes.find(t => t.uuid === uuid)
      let pending_uploads = this.uploads.filter(u => u.state === 'pending')
      let current_uploads = this.uploads.filter(u => u.state === 'current')
      let finished_uploads = this.uploads.filter(u => u.state === 'finished')

      if (this.selected_telescope) {
        this.selected_night_log = this.night_logs.find(nl => nl.telescope === uuid)
        this.filtered_pending_uploads = pending_uploads.filter(u => u.telescope['uuid'] === this.selected_telescope['uuid'])
        this.filtered_current_uploads = current_uploads.filter(u => u.telescope['uuid'] === this.selected_telescope['uuid'])
        this.filtered_finished_uploads = finished_uploads.filter(u => u.telescope['uuid'] === this.selected_telescope['uuid'])
      } else {
        this.selected_night_log = null
        this.filtered_pending_uploads = pending_uploads
        this.filtered_current_uploads = current_uploads
        this.filtered_finished_uploads = finished_uploads
      }
      if (this.selected_night_log) {
        this.selected_night_log_url = 'data/' + this.selected_night_log['date'].replace(/-/gi, '/')
      } else if (this.night_logs.length > 0) {
        this.selected_night_log_url = 'data/' + this.night_logs[0]['date'].replace(/-/gi, '/')
      } else {
        this.selected_night_log_url = ''
      }
      this.$forceUpdate()
    },
    getFormatedSize (bytes, decimals) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const dm = decimals || 2
      const sizes = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
    }
  }
})


