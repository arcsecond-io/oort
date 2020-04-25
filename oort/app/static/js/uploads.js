var app = new Vue({
  el: '#vuejs',
  data: {
    state: { showTables: false },
    messages: {},
    telescopes: [],
    night_logs: [],
    selected_telescope: null,
    selected_night_log: null,
    selected_night_log_url: '',
    current_uploads: [],
    finished_uploads: [],
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

      self.current_uploads = json.current_uploads
      self.finished_uploads = json.finished_uploads

      self.current_uploads.sort((u1, u2) => new Date(u1.started).getDate() < new Date(u2.started).getDate())
      self.finished_uploads.sort((u1, u2) => new Date(u1.ended).getDate() < new Date(u2.ended).getDate())

      const bars = document.getElementsByClassName('progress-bar')
      self.current_uploads.forEach((upload, index) => {
        let bar = bars[index]
        if (bar) {
          bar.style.width = upload.progress.toFixed(1).toString() + '%'
        }
      })

      if (self.selected_telescope) {
        self.filtered_current_uploads = self.current_uploads.filter(u => u.telescope['uuid'] === self.selected_telescope['uuid'])
        self.filtered_finished_uploads = self.finished_uploads.filter(u => u.telescope['uuid'] === self.selected_telescope['uuid'])
      } else {
        self.filtered_current_uploads = self.current_uploads
        self.filtered_finished_uploads = self.finished_uploads
      }
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
      if (this.selected_telescope) {
        this.selected_night_log = this.night_logs.find(nl => nl.telescope === uuid)
        this.filtered_current_uploads = this.current_uploads.filter(u => u.telescope['uuid'] === this.selected_telescope['uuid'])
        this.filtered_finished_uploads = this.finished_uploads.filter(u => u.telescope['uuid'] === this.selected_telescope['uuid'])
      } else {
        this.selected_night_log = null
        this.filtered_current_uploads = this.current_uploads
        this.filtered_finished_uploads = this.finished_uploads
      }
      if (this.selected_night_log) {
        this.selected_night_log_url = 'data/' + this.selected_night_log['date'].replace(/-/gi, '/')
      } else if (this.night_logs.length > 0) {
        this.selected_night_log_url = 'data/' + this.night_logs[0]['date'].replace(/-/gi, '/')
      } else {
        this.selected_night_log_url = ''
      }
      this.$forceUpdate()
    }
  }
})


