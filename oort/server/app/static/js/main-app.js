Vue.component('v-select', VueSelect.VueSelect)

var app = new Vue({
  el: '#vuejs',
  data: {
    source: null,
    state: { folders: [] },
    selected_folder: null,
    pending_uploads: [],
    current_uploads: [],
    finished_uploads: [],
    error_uploads: [],
    progresses: [],
    messages: {},
    telescopes: [],
    night_logs: []
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
      self.error_uploads = json_data.errors

      self.progresses = self.current_uploads.map(upload => upload.progress)
    }
  }
})


