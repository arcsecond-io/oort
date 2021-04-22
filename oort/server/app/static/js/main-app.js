Vue.component('v-select', VueSelect.VueSelect)

var app = new Vue({
  el: '#vuejs',
  data: {
    source: null,
    has_data: false,
    counts: null,
    state: { folders: [] },
    selected_folder: null,
    pending_uploads: [],
    current_uploads: [],
    finished_uploads: [],
    error_uploads: [],
    progresses: [],
    show_tables: {
      pending: true,
      current: true,
      finished_done: true,
      finished_skipped: true,
      error: true
    }
  },
  mounted () {
    const self = this
    this.source = new EventSource('/uploads')
    this.source.onmessage = function (event) {
      const json_data = JSON.parse(event.data)
      self.has_data = true

      self.state = json_data.state
      self.counts = json_data.counts
      if (!self.selected_folder && self.state.folders.length > 0) {
        self.selectFolder(self.state.folders[0])
      }

      self.current_uploads = json_data.current || []
      self.progresses = (self.current_uploads || []).map(u => u.progress)

      self.pending_uploads = json_data.pending || []
      self.error_uploads = json_data.errors || []
      self.finished_uploads = (json_data.finished || [])
        .filter(u => (u.substatus.toLowerCase().startsWith('skipped') && self.show_tables.finished_skipped) ||
          (!u.substatus.toLowerCase().startsWith('skipped') && self.show_tables.finished_done))
    }
  },
  methods: {
    selectFolder (folder) {
      this.reset()
      this.selected_folder = folder
      fetch('/update?selectedFolder=' + encodeURIComponent(folder.section))
    },
    reset () {
      this.pending_uploads = []
      this.current_uploads = []
      this.finished_uploads = []
      this.error_uploads = []
      this.progresses = []
      this.counts = null
    },
    retryAllFailed () {
      fetch('/retry?ids=' + this.error_uploads.reduce((acc, value) => acc + value.id.toString() + ',', ''))
    }
  }
})


