var app = new Vue({
  el: '#vuejs',
  data: {
    state: { showTables: false },
    messages: {},
    telescopes: [],
    night_logs: [],
    current_uploads: [],
    finished_uploads: [],
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
      self.night_logs = json.night_logs

      // self.admin = json.admin
      // if (self.admin['selected_night_log']) {
      //   self.admin['selected_night_log_url'] = 'data/' + self.admin['selected_night_log']['date'].replace(/-/gi, '/')
      // }
      // if (self.admin.close) {
      //   self.source.close()
      //   self.source.onmessage = null
      //   self.source = null
      // }
      //
      // self.current_uploads = json.current_uploads
      // self.finished_uploads = json.finished_uploads
      //
      // self.current_uploads.sort((u1, u2) => new Date(u1.started).getDate() < new Date(u2.started).getDate())
      // self.finished_uploads.sort((u1, u2) => new Date(u1.ended).getDate() < new Date(u2.ended).getDate())
      //
      // const bars = document.getElementsByClassName('progress-bar')
      // self.current_uploads.forEach((upload, index) => {
      //   let bar = bars[index]
      //   if (bar) {
      //     bar.style.width = upload.progress.toFixed(1).toString() + '%'
      //   }
      // })
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
      // this.admin['selected_telescope'] = (uuid === '__all__') ? null : this.admin.telescopes.find(t => t.uuid === uuid)
      // if (this.admin['selected_telescope']) {
      //   this.admin['selected_night_log'] = this.admin.night_logs.find(nl => nl.telescope === uuid)
      // } else {
      //   this.admin['selected_night_log'] = null
      // }
      // if (this.admin['selected_night_log']) {
      //   window.localStorage.setItem('selected_night_log', JSON.stringify(this.admin['selected_night_log']))
      // } else {
      //   window.localStorage.removeItem('selected_night_log')
      // }
      // if (this.admin.night_logs.length) {
      //   this.admin['selected_night_log_url'] = 'data/' + this.admin.night_logs[0]['date'].replace(/-/gi, '/')
      // } else {
      //   this.admin['selected_night_log_url'] = ''
      // }
      // this.$forceUpdate()
    }
  }
})


