var admin = new Vue({
  el: '#admin',
  data: {
    admin: null,
    source: null
  },
  mounted: function () {
    const self = this
    this.source = new EventSource('/admin')
    this.source.onmessage = function (event) {
      const json = JSON.parse(event.data)
      self.admin = json.admin
      if (self.admin['selected_night_log']) {
        self.admin['selected_night_log_url'] = 'data/' + self.admin['selected_night_log']['date'].replace(/-/gi, '/')
      }
      if (self.admin.close) {
        self.source.close()
        self.source.onmessage = null
        self.source = null
      }
    }
  },
  methods: {
    selectTelescope (uuid) {
      this.admin['selected_telescope'] = (uuid === '__all__') ? null : this.admin.telescopes.find(t => t.uuid === uuid)
      if (this.admin['selected_telescope']) {
        this.admin['selected_night_log'] = this.admin.night_logs.find(nl => nl.telescope === uuid)
      } else {
        this.admin['selected_night_log'] = null
      }
      if (this.admin['selected_night_log']) {
        window.localStorage.setItem('selected_night_log', JSON.stringify(this.admin['selected_night_log']))
      } else {
        window.localStorage.removeItem('selected_night_log')
      }
      if (this.admin.night_logs.length) {
        this.admin['selected_night_log_url'] = 'data/' + this.admin.night_logs[0]['date'].replace(/-/gi, '/')
      } else {
        this.admin['selected_night_log_url'] = ''
      }
      this.$forceUpdate()
    }
  }
})


