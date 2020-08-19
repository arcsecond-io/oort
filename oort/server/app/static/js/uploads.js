Vue.component('v-select', VueSelect.VueSelect)

var app = new Vue({
  el: '#vuejs',
  data: {
    source: null,
    loopID: null,
    state: { folders: [] },
    selected_folder: null,
    pending_uploads: [],
    current_uploads: [],
    finished_uploads: [],
    error_uploads: [],
    messages: {},
    telescopes: [],
    night_logs: []
  },
  beforeDestroy () {
    clearInterval(this.loopID)
  },
  computed: {
    selectButtonTitle () {
      return this.selected_folder ? this.selected_folder.path : '-'
    }
  },
  mounted: function () {
    const self = this
    this.source = new EventSource('/uploads')
    this.source.onmessage = function (event) {
      const json_data = JSON.parse(event.data)

      self.state = json_data.state
      if (self.state.folders.length === 1) {
        self.selected_folder = self.state.folders[0]
      }

      self.pending_uploads = json_data.pending
      self.current_uploads = json_data.current
      self.finished_uploads = json_data.finished
      self.error_uploads = json_data.error

      const bars = document.getElementsByClassName('progress-bar')
      self.current_uploads.forEach((upload, index) => {
        let bar = bars[index]
        if (bar) {
          bar.style.width = upload.progress.toFixed(1).toString() + '%'
        }
      })
    }
  },
  methods: {
    getFormattedSize (bytes, decimals) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const dm = decimals || 2
      const sizes = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
    }
  }
})


