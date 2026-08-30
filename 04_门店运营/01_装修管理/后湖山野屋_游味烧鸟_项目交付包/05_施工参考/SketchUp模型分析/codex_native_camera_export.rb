require 'sketchup.rb'
require 'fileutils'

module CodexNativeCameraExport
  extend self

  OUTPUT_DIR = 'C:/Users/admin/Documents/Codex/2026-08-06/referenced-chatgpt-conversation-this-is-an/outputs/后湖山野屋_游味烧鸟_项目交付包/05_施工参考/SketchUp模型分析/SketchUp原生机位底图'.freeze
  LOG_PATH = File.join(OUTPUT_DIR, '原生机位导出日志.txt').freeze
  TARGET_MODEL = 'D:/桌面/改造方案.skp'.freeze

  CAMERAS = [
    {
      name: '01_主视角_SKP原生视口.png',
      eye_cm: [580.0, -850.0, 175.0],
      target_cm: [580.0, 190.0, 105.0],
      fov: 52.0
    },
    {
      name: '02_沙发区_SKP原生视口.png',
      eye_cm: [650.0, -50.0, 185.0],
      target_cm: [380.0, 370.0, 78.0],
      fov: 66.0
    },
    {
      name: '03_坐在板前_SKP原生视口.png',
      eye_cm: [680.0, 175.0, 155.0],
      target_cm: [1055.0, 175.0, 95.0],
      fov: 66.0
    }
  ].freeze

  def point_from_cm(values)
    Geom::Point3d.new(values[0].cm, values[1].cm, values[2].cm)
  end

  def write_log(lines)
    FileUtils.mkdir_p(OUTPUT_DIR)
    File.open(LOG_PATH, 'a:utf-8') { |file| lines.each { |line| file.puts(line) } }
  rescue StandardError
    nil
  end

  def export_views
    model = Sketchup.active_model
    view = model.active_view
    FileUtils.mkdir_p(OUTPUT_DIR)

    rendering = model.rendering_options
    rendering['EdgeDisplayMode'] = 1 if rendering.respond_to?(:[]=)
    rendering['DrawSilhouettes'] = true if rendering.respond_to?(:[]=)
    rendering['DisplayFog'] = false if rendering.respond_to?(:[]=)
    rendering['BackgroundColor'] = Sketchup::Color.new(238, 232, 219) if rendering.respond_to?(:[]=)

    lines = ["开始导出: #{Time.now}", "模型: #{model.path}"]
    CAMERAS.each do |item|
      eye = point_from_cm(item[:eye_cm])
      target = point_from_cm(item[:target_cm])
      camera = Sketchup::Camera.new(eye, target, Geom::Vector3d.new(0, 0, 1), true)
      camera.fov = item[:fov]
      view.camera = camera
      view.invalidate
      view.refresh
      output_path = File.join(OUTPUT_DIR, item[:name])
      ok = view.write_image(
        filename: output_path,
        width: 1800,
        height: 1100,
        antialias: true,
        transparent: false
      )
      lines << "#{item[:name]}: #{ok ? '成功' : '失败'} | eye=#{item[:eye_cm]} target=#{item[:target_cm]}"
    end
    lines << "完成: #{Time.now}"
    write_log(lines)
  rescue StandardError => error
    write_log(["导出异常: #{error.class}: #{error.message}", *error.backtrace])
  ensure
    UI.start_timer(2.0, false) { Sketchup.quit }
  end

  unless file_loaded?(__FILE__)
    FileUtils.mkdir_p(OUTPUT_DIR)
    File.write(LOG_PATH, "插件载入: #{Time.now}\n", mode: 'a:utf-8')
    UI.start_timer(18.0, false) { export_views }
    file_loaded(__FILE__)
  end
end
